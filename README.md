# HarryPotter_Cloak

Hey Folks,

This is my project of making Invisible Cloak using an **Image Processing** technique called **Colour Detection and Segmentation**. I have implemented this using Python and OpenCV.

colour detection and segmentation: Colour detection is the process of detecting the name of any color.


We first have to take a single color cloth that must not contain any other color. I used a green color cloth for my project.
We then install openCV and implement the following steps:
1.Initialize the camera.<br>
2.Capture and Store a single frame(background) before starting.<br>
3.Detect the color of the cloth and create a mask.<br>
4.Apply the mask on frames.<br>
5.Combine the masked frames together.<br>
6.Remove the unnecessary noise from masks.<br>

