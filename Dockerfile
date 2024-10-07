# Step 1: Use the official Python 3.10.12 image as a base
FROM python:3.10.12

# Step 2: Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Step 3: Set the working directory
WORKDIR /app

# Step 4: Copy the requirements.txt into the container
COPY requirements.txt /app/

# Step 5: Install the dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Step 6: Copy the entire project into the container
COPY . /app/

# Step 7: Expose the necessary port
EXPOSE 8000

# Step 8: Run the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
