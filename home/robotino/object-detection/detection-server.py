import socket
import select
import cv2
import numpy as np
import io
from ultralytics import YOLO
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
#       7 Deactivate Detection Stream Message
#       8 Switch-to Workpiece Detection Message
#       9 Switch-to Conveyor Detection Message
#       10 Switch-to Slide Detection Message
#       11 Switch-off Detection Message
#   Extended Control Messages (payload 1 Float value (4 Bytes))
#       12 Set the confidence threshold for detection
#       13 Set the IOU for detection
"""

PICAM = False
if "rpi" in os.uname()[2]:
    PICAM = True

if PICAM:
    import picamera2 as picamera

IMSHOW = False
STREAM_RAW = True
STREAM_MARKED = True
DETECT = False
OBJECT = 2
CONFIDENCE_THRESHOLD = 0.2
IOU = 0.3
ROTATION = 270
OLD_PPX = 247.16991942710536
OLD_PPY = 311.0215589376087
OLD_F_Y = 761.4091782824479
OLD_F_X = 762.6983388147113
NEW_PPX = 251.00801023972
NEW_PPY = 301.32794812152997
NEW_F_Y = 634.6348457656962
NEW_F_X = 642.6147379302428
K1 = -0.50304233
K2 = 0.5782515
K3 = -0.00701836
K4 = 0.00308524
K5 = -0.71367181

 # model = YOLO('model.pt',task='detect')
 # model.export(format="ncnn")
ncnn_model = YOLO('model_ncnn_model', task='detect')

def send_to_all(clients, message):
    for client_socket in clients:
        client_socket.sendall(message)

def send_frame_to_all(clients, frame, timestamp, msg_type):
    # convert the frame to a JPEG image and encode it as base64
    _, frame_arr = cv2.imencode('.jpg', frame)
    frame_bytes = frame_arr.tobytes()
    frame_b64 = base64.b64encode(frame_bytes)

    # create a message type 1/2 header
    header = struct.pack('!BQIII', msg_type, timestamp, frame.shape[0], frame.shape[1], len(frame_b64))

    # build the message
    message = header + frame_b64

    # broadcast the message
    send_to_all(clients, message)

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
                        message = client.recv(9)
                        if not message:
                            clients.remove(client)
                            notifiers.remove(client)
                        else:
                            message_type, timestamp = struct.unpack('Bq', message[:9])
                            print("Received control message of type ", message_type)
                            if message_type == 4:
                                STREAM_RAW = True
                            if message_type == 5:
                                STREAM_MARKED = True
                            elif message_type == 6:
                                STREAM_RAW = False
                            elif message_type == 7:
                                STREAM_MARKED = False
                            elif message_type == 8:
                                DETECT = True
                                OBJECT = 2
                            elif message_type == 9:
                                DETECT = True
                                OBJECT = 0
                            elif message_type == 10:
                                DETECT = True
                                OBJECT = 1
                            elif message_type == 11:
                                DETECT = False
                            elif message_type == 12:
                                message = client.recv(4)
                                CONFIDENCE_THRESHOLD = struct.unpack('f', message[0:4])
                            elif message_type == 13:
                                message = client.recv(4)
                                IOU = struct.unpack('f', message[0:4])
                            elif message_type == 14:
                                message = client.recv(56)
                                ROTATION = struct.unpack('I', message[0:4])
                                OLD_PPX = struct.unpack('f', message[4:8])
                                OLD_PPY = struct.unpack('f', message[8:12])
                                OLD_F_Y = struct.unpack('f', message[12:16])
                                OLD_F_X = struct.unpack('f', message[16:20])
                                NEW_PPX = struct.unpack('f', message[20:24])
                                NEW_PPY = struct.unpack('f', message[24:28])
                                NEW_F_Y = struct.unpack('f', message[28:32])
                                NEW_F_X = struct.unpack('f', message[32:36])
                                K1 = struct.unpack('f', message[36:40])
                                K2 = struct.unpack('f', message[40:44])
                                K3 = struct.unpack('f', message[44:48])
                                K4 = struct.unpack('f', message[48:52])
                                K5 = struct.unpack('f', message[52:56])

                
                for client in exception_sockets:
                    print("removing socket with exception")
                    clients.remove(client)
                    notifiers.remove(client)

                # get a frame from the camera + timestamp
                frame = None
                if PICAM:
                    frame = cam.capture_array()
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    # preprocessing
                    # rotation
                    if(ROTATION == 270):
                        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
                    elif(ROTATION == 90):
                        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                    elif(ROTATION == 180):
                        frame = cv2.rotate(frame, cv2.ROTATE_180)

                    # undistort
                    old_camera_matrix = cv2.UMat(np.array([[OLD_F_X, 0., OLD_PPX], [0., OLD_F_Y, OLD_PPY], [0., 0., 1.]]))
                    new_camera_matrix = cv2.UMat(np.array([[NEW_F_X, 0., NEW_PPX], [0., NEW_F_Y, NEW_PPY], [0., 0., 1.]]))
                    distortion = cv2.UMat(np.array([[K1, K2, K3, K4, K5]]))
                    frame =  cv2.UMat.get(cv2.undistort(frame, old_camera_matrix, distortion, None, new_camera_matrix))
                else:
                    check, frame = cam.read()
                timestamp = int(time.time_ns())
                # the camera feed is streamed to all connected clients
                if STREAM_RAW:
                    send_frame_to_all(clients, frame, timestamp, 1)

                # the detection is supposed to run and the results will be sent to all connected clients
                if DETECT:
                    results=ncnn_model.track(frame, persist=True, iou=IOU)
                    if STREAM_MARKED:
                        send_frame_to_all(clients, results[0].plot(), timestamp, 2)
        
                    boxes = results[0].boxes 
                    confidences = results[0].boxes.conf
                    class_ids = results[0].boxes.cls
                    shapes = results[0].boxes.xywh.numpy()
                    
                    # Filter detections
                    filtered_indices = [
                        i for i, conf in enumerate(confidences)
                        if conf >= CONFIDENCE_THRESHOLD and class_ids[i] == OBJECT
                    ]

                    # Create a copy of the frame to plot filtered results
                    filtered_frame = frame.copy()
                    for i in filtered_indices:
                        box = boxes[i]
                        class_id = class_ids[i]
                        x=shapes[i][0]
                        y=shapes[i][1]
                        w=shapes[i][2]
                        h=shapes[i][3]

                        detection_message = struct.pack('!BQfffffI', 3, timestamp, x, y, w, h, float(confidences[i]), int(class_id))
                        send_to_all(clients,detection_message)

                if IMSHOW:
                    cv2.imshow('video', frame)
                    key = cv2.waitKey(1)
                    if key == 27:
                        break
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(e)
                print("Error during transmission")
                time.sleep(0.1)

        
    except Exception as e: 
        print("Exception occured, closing gracefully")
        print(e)
        
        # close camera
        # cam.release()
        cv2.destroyAllWindows()
        print("Camera closed")

        # close server socket
        server.shutdown()
        server.close()
        print("Server closed")

except Exception as e: 
    print("Exception occured, closing gracefully")
    print(e)
