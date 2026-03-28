import docker
import json
import random
import string
from datetime import datetime, timedelta
from flask import current_app
from models import Lab, LabInstance, User, db
import logging

logger = logging.getLogger(__name__)

class LabManager:
    def __init__(self):
        try:
            # Try to connect using Unix socket first
            self.docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')
            self.docker_client.ping()
        except Exception as e:
            try:
                # Fallback to environment variables
                self.docker_client = docker.from_env()
                self.docker_client.ping()
            except Exception as e2:
                logger.error(f"Failed to connect to Docker: {e2}")
                self.docker_client = None

    def create_lab_instance(self, lab_id, user_id):
        """Create a new lab instance for a user"""
        if not self.docker_client:
            raise Exception("Docker client not available")
        
        lab = Lab.query.get(lab_id)
        if not lab:
            raise Exception("Lab not found")
        
        user = User.query.get(user_id)
        if not user:
            raise Exception("User not found")
        
        # Check if user already has an active instance
        existing_instance = LabInstance.query.filter_by(
            lab_id=lab_id, 
            user_id=user_id, 
            is_active=True
        ).first()
        
        if existing_instance:
            # Check if instance is still valid
            if existing_instance.expires_at and existing_instance.expires_at > datetime.utcnow():
                return existing_instance
            else:
                # Deactivate expired instance
                existing_instance.is_active = False
                db.session.commit()
        
        # Generate unique container name
        container_name = f"lab_{lab_id}_{user_id}_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"
        
        try:
            # Prepare environment variables
            environment = {
                'LAB_ID': str(lab_id),
                'USER_ID': str(user_id),
                'FLAG': lab.flag
            }
            
            # Prepare port mappings
            ports = {}
            if lab.target_port:
                ports[f"{lab.target_port}/tcp"] = None  # Random host port
            
            # Create container
            if lab.docker_compose:
                # Handle docker-compose
                container = self._create_from_compose(lab, container_name, environment)
            else:
                # Handle single image
                container = self.docker_client.containers.run(
                    lab.docker_image or 'ctf/base:latest',
                    name=container_name,
                    detach=True,
                    environment=environment,
                    ports=ports,
                    mem_limit='512m',
                    cpu_quota=50000,  # Limit CPU usage
                    network='ctf-network' if self._network_exists('ctf-network') else None
                )
            
            # Get container info
            container.reload()
            container_info = container.attrs
            
            # Create lab instance record
            lab_instance = LabInstance(
                lab_id=lab_id,
                user_id=user_id,
                container_id=container.id,
                container_ip=self._get_container_ip(container),
                container_port=self._get_container_port(container, lab.target_port),
                expires_at=datetime.utcnow() + timedelta(hours=4) if lab.time_limit else None
            )
            
            db.session.add(lab_instance)
            db.session.commit()
            
            logger.info(f"Created lab instance: {container_name} for user {user.username}")
            return lab_instance
            
        except Exception as e:
            logger.error(f"Failed to create lab instance: {e}")
            raise Exception(f"Failed to create lab instance: {str(e)}")

    def stop_lab_instance(self, instance_id):
        """Stop and remove a lab instance"""
        instance = LabInstance.query.get(instance_id)
        if not instance:
            raise Exception("Lab instance not found")
        
        try:
            if instance.container_id:
                container = self.docker_client.containers.get(instance.container_id)
                container.stop()
                container.remove()
                logger.info(f"Stopped container: {instance.container_id}")
            
            instance.is_active = False
            db.session.commit()
            
        except docker.errors.NotFound:
            logger.warning(f"Container {instance.container_id} not found")
            instance.is_active = False
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to stop lab instance: {e}")
            raise

    def reset_lab_instance(self, instance_id):
        """Reset a lab instance"""
        instance = LabInstance.query.get(instance_id)
        if not instance:
            raise Exception("Lab instance not found")
        
        # Stop current instance
        self.stop_lab_instance(instance_id)
        
        # Create new instance
        return self.create_lab_instance(instance.lab_id, instance.user_id)

    def get_instance_logs(self, instance_id):
        """Get logs for a lab instance"""
        instance = LabInstance.query.get(instance_id)
        if not instance:
            raise Exception("Lab instance not found")
        
        try:
            container = self.docker_client.containers.get(instance.container_id)
            logs = container.logs(tail=100).decode('utf-8')
            return logs
        except Exception as e:
            logger.error(f"Failed to get instance logs: {e}")
            return "Logs not available"

    def cleanup_expired_instances(self):
        """Clean up expired lab instances"""
        expired_instances = LabInstance.query.filter(
            LabInstance.expires_at < datetime.utcnow(),
            LabInstance.is_active == True
        ).all()
        
        for instance in expired_instances:
            try:
                self.stop_lab_instance(instance.id)
                logger.info(f"Cleaned up expired instance: {instance.id}")
            except Exception as e:
                logger.error(f"Failed to cleanup instance {instance.id}: {e}")

    def get_container_stats(self, instance_id):
        """Get container statistics"""
        instance = LabInstance.query.get(instance_id)
        if not instance:
            raise Exception("Lab instance not found")
        
        try:
            container = self.docker_client.containers.get(instance.container_id)
            stats = container.stats(stream=False)
            return stats
        except Exception as e:
            logger.error(f"Failed to get container stats: {e}")
            return None

    def _create_from_compose(self, lab, container_name, environment):
        """Create container from docker-compose"""
        # This is a simplified version - in production, you'd use docker-compose
        # For now, we'll parse the compose file and create containers manually
        try:
            compose_data = json.loads(lab.docker_compose)
            # Implementation would depend on compose structure
            # For now, create a basic container
            return self.docker_client.containers.run(
                'ctf/base:latest',
                name=container_name,
                detach=True,
                environment=environment
            )
        except Exception as e:
            logger.error(f"Failed to create from compose: {e}")
            raise

    def _network_exists(self, network_name):
        """Check if Docker network exists"""
        try:
            self.docker_client.networks.get(network_name)
            return True
        except docker.errors.NotFound:
            return False

    def _get_container_ip(self, container):
        """Get container IP address"""
        try:
            container.reload()
            networks = container.attrs['NetworkSettings']['Networks']
            if networks:
                # Get first network's IP
                network_name = list(networks.keys())[0]
                return networks[network_name]['IPAddress']
        except Exception as e:
            logger.error(f"Failed to get container IP: {e}")
        return None

    def _get_container_port(self, container, target_port):
        """Get mapped container port"""
        try:
            container.reload()
            port_bindings = container.attrs['NetworkSettings']['Ports']
            if port_bindings and f"{target_port}/tcp" in port_bindings:
                host_bindings = port_bindings[f"{target_port}/tcp"]
                if host_bindings:
                    return host_bindings[0]['HostPort']
        except Exception as e:
            logger.error(f"Failed to get container port: {e}")
        return None

    def get_active_instances_count(self):
        """Get count of active lab instances"""
        return LabInstance.query.filter_by(is_active=True).count()

    def get_user_active_instances(self, user_id):
        """Get all active instances for a user"""
        return LabInstance.query.filter_by(
            user_id=user_id, 
            is_active=True
        ).all()

# Global lab manager instance
lab_manager = LabManager()
