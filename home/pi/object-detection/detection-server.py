import socket
import select
import cv2
import numpy as np
import io
import base64
import struct
import time
import os

"""
# Message Format
#   Header
#     Type (1 Byte)
#     Time Stamp (8 Bytes)
#
# Message Types
#   Data Messages (payload)
#       1 Raw Frame Message AND 2 Detection Frame Message
#           Image Width (4 Bytes)
#           Image Height (4 Bytes)
#           JPEG array length (4 Bytes)
#           Image, OpenCV image array as Base64
#       3 Detection Message (representing one object's bounding box)
#           x (4 Bytes)
#           y (4 Bytes)
#           h (4 Bytes)
#           w (4 Bytes)
#           accuracy (4 Bytes, float)
#           class (4 Bytes)
#   Control Messages (no payload)
#       4 Activate Stream Message
#       5 Activate Detection Stream Message
#       6 Deactivate Stream Message
#       7 Switch-to Workpiece Detection Message
#       8 Switch-to Conveyor Detection Message
#       9 Switch-to Slide Detection Message 
#       10 Switch-off Detection Message
"""

IMSHOW = False
PICAM = False
if "rpi" in os.uname()[2]:
    PICAM = True

if PICAM:
    import picamera2 as picamera

STREAM_RAW = True
STREAM_MARKED = False
DETECT = True
OBJECT = "workpiece"

def send_to_all(clients, message):
    for client_socket in clients:
        client_socket.sendall(message)

try:
    cam = None
    if PICAM:
        cam = picamera.Picamera2()
        cam.start()
    else:
        cam = cv2.VideoCapture(0)

    print("set up camera")
    try:
        # create a socket object
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("0.0.0.0", 6465))
        server.listen(0)

        clients = []
        notifiers = [server]


        while True:
            try:
                notifying_sockets, _, exception_sockets = select.select(notifiers, [], [], 0)

                # process all notifying and excepting sockets at the begin of every iteration
                for client in notifying_sockets:
                    if client == server:
                        client_socket, _ = server.accept()
                        notifiers.append(client_socket)
                        clients.append(client_socket)
                        print("Connection established")
                    else:
                        message = client.recv(2048)
                        if not message:
                            clients.remove(client)
                            notifiers.remove(client)
                        else:
                            message_type, timestamp = struct.unpack('Bq', message[:9])
                            print("Received control message of type ", message_type)
                            if message_type == 4:
                                STREAM_RAW = True
                                STREAM_MARKED = False
                            if message_type == 5:
                                STREAM_RAW = False
                                STREAM_MARKED = True
                            elif message_type == 6:
                                STREAM_RAW = False
                                STREAM_MARKED = False
                            elif message_type == 7:
                                DETECT = True
                            elif message_type == 8:
                                DETECT = True
                                OBJECT = "workpiece"
                            elif message_type == 9:
                                DETECT = True
                                OBJECT = "conveyor"
                            elif message_type == 10:
                                DETECT = False
                                OBJECT = "slide"
                for client in exception_sockets:
                    print("removing socket with exception")
                    clients.remove(client)
                    notifiers.remove(client)

                # get a frame from the camera + timestamp
                frame = None
                if PICAM:
                    frame = cam.capture_array()
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                else:
                    check, frame = cam.read()
                timestamp = int(time.time())
                # the camera feed is streamed to all connected clients
                if STREAM_RAW:
                    # convert the video frame to a jpg encoded as b64
                    _, frame_arr = cv2.imencode('.jpg', frame) 
                    frame_bytes = frame_arr.tobytes()
                    frame_b64 = base64.b64encode(frame_bytes)

                    # create a message type 1 header
                    header = struct.pack('!BIIII', 1, timestamp, frame.shape[0], frame.shape[1], len(frame_b64))

                    # build the message
                    message = header + frame_b64

                    # broadcast the message
                    send_to_all(clients, message)

                # the detection is supposed to run and the results will be sent to all connected clients
                if DETECT:

                    #!!!!! RUN THE DETECTION HERE !!!!!

                    if STREAM_MARKED:
                        #!!!!! SEND THE PICTURE WITH THE BOUNDING BOXES THE SAME WAY IT IS DONE FOR STREAM_RAW HERE
                        print("Streaming pictures with detection mark for debugging")

                    #!!!!! SEND THE DATA FOR EACH BOUNDING BOX HERE !!!!!
                    #for detection in detected:
                    # send a detection message
                    #detection_message = struct.pack('!BIIIIIfI', 3, timestamp, x, y, h, w, acc, cls)
                    #send_to_all(clients, detection_message)

                if IMSHOW:
                    cv2.imshow('video', frame)
                    key = cv2.waitKey(1)
                    if key == 27:
                        break

            except KeyboardInterrupt:
                break
            except:
                print("Error during transmission")
                time.sleep(0.1)


    except Exception as e: 
        print("Exception occured, closing gracefully")
        print(e)
        
        # close camera
        cam.release()
        cv2.destroyAllWindows()
        print("Camera closed")

        # close server socket
        server.close()
        print("Server closed")

except Exception as e: 
    print("Exception occured, closing gracefully")
    print(e)