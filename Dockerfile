
# Gunakan image Python
FROM python:3.10-slim

# Set workdir
WORKDIR /app

# Copy file requirement.txt ke container
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy semua file ke container
COPY . .

# Expose port yang akan digunakan Django
EXPOSE 8000

# Jalankan perintah untuk menjalankan server Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
