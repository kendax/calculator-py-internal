# Using python 3.7 as the base image
FROM python:3.7

# Install django
RUN pip install django

# Mount the project files to the image
COPY . code
WORKDIR /code

# Open up port 8000 in the container
EXPOSE 8000

# Create tables in the project database
RUN python /code/calcpy/manage.py migrate

# runs the production server
ENTRYPOINT ["python", "calcpy/manage.py"]
CMD ["runserver", "0.0.0.0:8000"]