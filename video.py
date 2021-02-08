import cv2
import pyfakewebcam
from filters import *

'''
You can use this for Zoom.
'''

'''removing:
    sudo modprobe -r v4l2loopback
    pip3 uninstall pyfakewebcam concurrent_videocapture
    sudo pacman -Rcns v4l2loopback-dkms opencv linux-headers zoom
'''

concurrent_videocapture = True
try:
  from concurrent_videocapture import ConcurrentVideoCapture
except:
  concurrent_videocapture = False

capture = ConcurrentVideoCapture if concurrent_videocapture else cv2.VideoCapture
# your actual camera
video_capture = capture(0)
ret, image = video_capture.read()

height, width = image.shape[:2] #usually 480, 640
ASPECT = 9/16 #480/640
h, w = int(width * ASPECT), width

# Create virtual camera object to stream images
stream_camera = pyfakewebcam.FakeWebcam(
    "/dev/video20", w, h
)


filter = 0
mod_var = 1
while True:
    ret, image = video_capture.read()

    ######## Whatever processing of the image
    i = Image.fromarray(image)
    i=i.crop((0, (i.height - i.width * ASPECT) // 2, i.width, (i.height - i.width * ASPECT) // 2 + i.width * ASPECT)) # crop the image to specified aspect ratio and center it
    #########################################

    key = cv2.waitKey(1)
    #if key != -1: print(key)
    if key == 27:  # ESC
        break
    elif key == ord('1'):
        filter = 1
    elif key == ord('2'):
        filter = 2
    elif key == ord('-'):
        mod_var /= 1.15
    elif key == ord('+'):
        mod_var *= 1.15
    elif key == ord('0'):#elif key != -1:
        filter = 0

    if filter == 1:
        i_mod = partition(1, int(6 * mod_var), i, 0.1)
    elif filter == 2:
        filter = 2
        i_mod = mosaic(int(40 * mod_var), i, 20)
    else:
        i_mod = i

    image = np.array(i_mod.resize((w,h), Image.NEAREST))
    cv2.imshow("video", image)
    # Write frame to virtual device
    stream_camera.schedule_frame(image[..., ::-1])

video_capture.release()
cv2.destroyAllWindows()
