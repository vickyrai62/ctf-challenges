# TODO: Add Media File Upload for Cryptography Challenges

## Tasks
- [x] Update Challenge model in models.py: Add media_files (JSON list of filenames) and crypto_type field
- [x] Create static/uploads/challenges/ directory for storing uploaded files
- [x] Modify add_challenge route in routes.py: Handle multipart file uploads, validate image formats, save files securely
- [x] Modify edit_challenge route in routes.py: Handle file uploads, allow adding/removing files
- [x] Update add_challenge.html template: Add multiple file input for images and crypto type select
- [x] Update edit_challenge.html template: Add file input, crypto type select, display existing uploaded files
- [x] Update challenge.html template: Display uploaded images for challenges
- [x] Test file upload functionality and ensure secure handling (validate extensions, prevent path traversal)
- [x] Add delete functionality for uploaded files if needed
- [x] Update database schema and reinitialize database
