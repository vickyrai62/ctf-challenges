from app import create_app
from models import User, Challenge

def init_db():
    app = create_app()
    with app.app_context():
        from extensions import db
        db.create_all()

        # Create admin user
        admin = User(username='admin', email='admin@example.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)

        # Sample challenges
        challenges = [
            Challenge(
                title='Welcome to CTF',
                description='Find the flag hidden in this message: The flag is AITCTF{welcome}',
                category='message encoding/decoding',
                flag='AITCTF{welcome}',
                points=10
            ),
            Challenge(
                title='Morse Code',
                description='Decode this Morse code: .... .. / .. ... / -- --- .-. ... . / -.-. --- -.. .\n\nFlag format: AITCTF{decoded_text}',
                category='morse code',
                flag='AITCTF{hiismorsecode}',
                points=20
            ),
            Challenge(
                title='QR Code',
                description='Scan this QR code: [Imagine a QR code here] The flag is AITCTF{qr_solved}',
                category='QR code',
                flag='AITCTF{qr_solved}',
                points=30
            ),
            Challenge(
                title='Hashing',
                description='What is the MD5 hash of "ctf"? The flag is AITCTF{md5_hash}',
                category='hashing',
                flag='AITCTF{9a3bf0856a1d18c3f8c1e0b8c1e0b8c}',
                points=25
            ),
            Challenge(
                title='Location',
                description='What is the capital of France? Flag: AITCTF{capital}',
                category='location',
                flag='AITCTF{paris}',
                points=15
            ),
            Challenge(
                title='Audio Challenge',
                description='Listen to this audio: [Imagine audio file] The flag is AITCTF{audio_flag}',
                category='audio',
                flag='AITCTF{audio_flag}',
                points=35
            ),
            Challenge(
                title='Car Riddle',
                description='What has wheels and flies but is not an airplane? Flag: AITCTF{answer}',
                category='car',
                flag='AITCTF{garbage_truck}',
                points=20
            ),
            Challenge(
                title='House of Secrets',
                description='Find the secret in the house: The flag is hidden in the basement. AITCTF{secret_room}',
                category='house of secrets',
                flag='AITCTF{secret_room}',
                points=40
            ),
            Challenge(
                title='Image Puzzle',
                description='Solve the puzzle in this image: [Imagine image] Flag: AITCTF{image_solved}',
                category='images',
                flag='AITCTF{image_solved}',
                points=30
            ),
            Challenge(
                title='Logo Recognition',
                description='What company does this logo represent? [Imagine logo] Flag: AITCTF{company}',
                category='logo',
                flag='AITCTF{google}',
                points=25
            )
        ]

        for challenge in challenges:
            db.session.add(challenge)

        db.session.commit()
        print("Database initialized with sample data.")

if __name__ == '__main__':
    init_db()
