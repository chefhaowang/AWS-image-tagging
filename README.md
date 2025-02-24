# AWS Cloud-Based Image Storage and Object Detection App

This is the project for building AWS service for a image storing and tagging application.


Here is what we have on in the root:
1. lambda: store all related lambda func and related files
2. frontend-project: frontend file using jquery, URL: https://frontend-bucket-67.s3.amazonaws.com/login.html

related arn for lambda layer setup:

1. object_detectioin(python 3.8 / x86_64):
   
opencv-python-headless: arn:aws:lambda:us-east-1:770693421928:layer:Klayers-python38-opencv-python-headless:11

numpy: arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p38-numpy:13

libgthread-so: arn:aws:lambda:us-east-1:770693421928:layer:Klayers-python38-libgthread-so:1
   
2. image-thumbnail(python 3.12 / x86_64):

pillow: arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p312-Pillow:2
   
Thanks to Klayers for providing Python package arns!!!🥰🥰🥰
