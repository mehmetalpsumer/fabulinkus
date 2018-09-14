# -*- coding: utf-8 -*-
from __future__ import division
from scipy.spatial import distance as dist
from imutils.video import FileVideoStream
from imutils.video import VideoStream
from imutils import face_utils
from word import Word
import numpy as np
import argparse
import imutils
import time
import dlib
import cv2
import random
import os
from pathlib import Path
import string
from skpy import Skype
from kivy.app import App
from kivy.properties import ObjectProperty, NumericProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from functools import partial
from kivy.uix.popup import Popup
from kivy.core.window import Window
import urllib
from Xlib import X, display
from pymouse import PyMouse
import thread
from kivy.properties import BooleanProperty
from kivy.base import runTouchApp

Window.size = (1366, 768)
Window.clearcolor = (10, 1, 1, 1)
isBlink = False
isSpaceClicked=False # for correcting to add auto complete word as new word
steptime = 1
global skypeobject
global alert_on
alert_on = False



class HoverBehavior(object):
    """Hover behavior.
    :Events:
        `on_enter`
            Fired when mouse enter the bbox of the widget.
        `on_leave`
            Fired when the mouse exit the widget
    """

    hovered = BooleanProperty(False)
    border_point= ObjectProperty(None)
    '''Contains the last relevant point received by the Hoverable. This can
    be used in `on_enter` or `on_leave` in order to know where was dispatched the event.
    '''

    def __init__(self, **kwargs):
        self.register_event_type('on_enter')
        self.register_event_type('on_leave')
        Window.bind(mouse_pos=self.on_mouse_pos)
        super(HoverBehavior, self).__init__(**kwargs)

    def on_mouse_pos(self, *args):
        if not self.get_root_window():
            return # do proceed if I'm not displayed <=> If have no parent
        pos = args[1]
        #Next line to_widget allow to compensate for relative layout
        inside = self.collide_point(*self.to_widget(*pos))
        if self.hovered == inside:
            #We have already done what was needed
            return
        self.border_point = pos
        self.hovered = inside
        if inside:
            self.dispatch('on_enter')
        else:
            self.dispatch('on_leave')

    def on_enter(self):
        pass

    def on_leave(self):
        pass
class AutoCompleteButton(Button, HoverBehavior):
    def __init__(self, **kwargs):
        super(AutoCompleteButton, self).__init__(**kwargs)
    def on_enter(self, *args):
        self.background_color = (1.0, 0.0, 0.0, 1.0)

    def on_leave(self, *args):
        self.background_color = (88.0, 88.0, 88.0)


class OptionsButtons(Button, HoverBehavior):
    def __init__(self, **kwargs):
        super(OptionsButtons, self).__init__(**kwargs)
    def on_enter(self, *args):
        self.background_color = (1.0, 0.0, 0.0, 1.0)

    def on_leave(self, *args):
        self.background_color = (88.0, 88.0, 88.0)


class AlphabetButtons(Button, HoverBehavior):
    def __init__(self, **kwargs):
        super(AlphabetButtons, self).__init__(**kwargs)
    def on_enter(self, *args):
        self.background_color = (1.0, 0.0, 0.0, 1.0)


    def on_leave(self, *args):
        self.background_color = (88.0, 88.0, 88.0)


class CameraCv:
    def eye_aspect_ratio(self, eye):
        # compute the euclidean distances between the two sets of
        # vertical eye landmarks (x, y)-coordinates
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])

        # compute the euclidean distance between the horizontal
        # eye landmark (x, y)-coordinates
        C = dist.euclidean(eye[0], eye[3])

        # compute the eye aspect ratio
        ear = (A + B) / (2.0 * C)

        # return the eye aspect ratio
        return ear

    def move_mouse_pointer(self, coor):
        # video = 640x480
        # 360-460 x range
        # 160-230 y range
        print("Coordinates: {}, Range X: {}, Range Y: {}".format(coor, self.X_RANGE, self.Y_RANGE))

        if coor[0] > self.X_RANGE[0] and coor[0] < self.X_RANGE[1] and coor[1] > self.Y_RANGE[0] and coor[1] < self.Y_RANGE[1]:
            scaled_x = ((coor[0] - self.X_RANGE[0]) / (self.X_RANGE[1] - self.X_RANGE[0])) * self.res_w
            scaled_y = ((coor[1] - self.Y_RANGE[0]) / (self.Y_RANGE[1] - self.Y_RANGE[0])) * self.res_h
            self.alert_flag = True

        else:
            if not alert_on:
                thread.start_new_thread(self.alert, (1, ))

            print("Out of range!")
            return None
        current_pos = [self.root.query_pointer()._data["root_x"],
                       self.root.query_pointer()._data["root_y"]]
        #print("Current mouse: {}, {}".format(current_pos[0], current_pos[1]))

        step_size_x = 1
        step_size_y = 1

        coor = [scaled_x, scaled_y]  # Scale
        print("Scaled coordinates: {}".format(coor))
        #print("x: {} => {}, y: {} => {}".format(coor[0], scaled_x, coor[1], scaled_y))

        delta_x = (coor[0] - current_pos[0]) / step_size_x
        delta_y = (coor[1] - current_pos[1]) / step_size_y
        #print("res_w: {} current_pos: {} delta_x: {}".format(res_w, current_pos[0], delta_x))
        self.root.warp_pointer(round(self.res_w - (current_pos[0] + delta_x)), round(current_pos[1] + delta_y))
        self.d.sync()

    def gaze_coordinate(self, left_eye, right_eye):
        # TODO; mean values
        left_x = left_eye[0][0][0]
        left_y = left_eye[0][0][1]
        right_x = right_eye[3][0][0]
        right_y = right_eye[3][0][1]

        total_x = 0
        total_y = 0

        for point in left_eye:
            total_x += point[0][0]
            total_y += point[0][1]
        for point in right_eye:
            total_x += point[0][0]
            total_y += point[0][1]

        x = total_x / (len(left_eye) + len(right_eye))
        y = total_y / (len(left_eye) + len(right_eye))

        print("{} {}".format(x, y))
        return [x, y]

    def within_range(self, target, current):
        if (target[0] + self.CLICK_RANGE >= current[0] >= target[0] - self.CLICK_RANGE
                and target[1] + self.CLICK_RANGE >= current[1] >= target[1] - self.CLICK_RANGE):
            return True
        else:
            return False

    def alert(self, sec):
        print("ALERT")
        global alert_on
        alert_on = True
        os.system("aplay alert.wav")
        time.sleep(1/sec)
        alert_on = False

    def __init__(self):
        # mouse
        self.alert_flag = False
        self.mouse = PyMouse()
        self.d = display.Display()
        self.res = self.d.screen().root.get_geometry()
        self.res_h = self.res.height
        self.res_w = self.res.width
        self.s = self.d.screen()
        self.root = self.s.root

        # define two constants, one for the eye aspect ratio to indicate
        # blink and then a second constant for the number of consecutive
        # frames the eye must be below the threshold
        self.EYE_AR_THRESH = 0.2
        self.EYE_AR_CONSEC_FRAMES = 20

        # initialize the frame counters and the total number of blinks
        self.COUNTER = 0
        self.TOTAL = 0

        # Click condition
        self.CLICK_CONSEC_FRAMES = 20
        self.CLICK_RANGE = 3
        self.CLICK_FRAME_COUNTER = 0
        self.initial_coor = None

        # Range to accept mouse movement
        self.X_RANGE = [230, 370]
        self.Y_RANGE = [130, 230]

        # initialize dlib's face detector (HOG-based) and then create
        # the facial landmark predictor
        print("[INFO] loading facial landmark predictor...")
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(
            'shape_predictor_68_face_landmarks.dat')

        # grab the indexes of the facial landmarks for the left and
        # right eye, respectively
        (self.lStart, self.lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
        (self.rStart,
         self.rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

        # start the video stream thread
        print("[INFO] starting video stream thread...")
        self.vs = VideoStream(0).start()

        self.fileStream = False
        print("Update")

class AlphabetAutoCompleteContainer(BoxLayout):
    def __init__(self, **kwargs):
        super(AlphabetAutoCompleteContainer, self).__init__(**kwargs)


class AutoCompleteWord(GridLayout):
    def __init__(self, **kwargs):
        super(AutoCompleteWord, self).__init__(**kwargs)


class OptionsWidget(BoxLayout):
    def __init__(self, **kwargs):
        super(OptionsWidget, self).__init__(**kwargs)


class LabelSentence(BoxLayout):

    def __init__(self, **kwargs):
        super(LabelSentence, self).__init__(**kwargs)


class AlphabetWidget(GridLayout):

    def __init__(self, **kwargs):
        super(AlphabetWidget, self).__init__(**kwargs)


class RootWidget(BoxLayout):

    global alphabet_container
    alphabet_container = AlphabetWidget()

    global autocomplete_container
    autocomplete_container = AutoCompleteWord()

    global sentence_container
    sentence_container = LabelSentence()
    global options_container
    options_container = OptionsWidget()

    def __init__(self, **kwargs):
        self.word = Word()
        self.camera = CameraCv()
        super(RootWidget, self).__init__(**kwargs)
        self.addOptionsButtonsToArray()
        self.addAlphabetButtonsToArray()
        username="fabulinkus2018@hotmail.com"
        password="gokturk1995"
        sk = Skype(username, password) # connect to Skype
        global skypeobject
        skypeobject = sk.contacts["gokturktopar"].chat # 1-to-1 conversation
        Clock.schedule_interval(self.update, 1.0 / 25)
        #Clock.schedule_interval(self.checkSkypeIncomingMessages,5)


    def update(self, dt):
        # if this is a file video stream, then we need to check if
        # there any more frames left in the buffer to process
        global isBlink
        frame = self.camera.vs.read()
        frame = imutils.resize(frame, width=450)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # detect faces in the grayscale frame
        rects = self.camera.detector(gray, 0)
        key = cv2.waitKey(1) & 0xFF
        # loop over the face detections
        for rect in rects:
            isBlink = False
            # determine the facial landmarks for the face region, then
            # convert the facial landmark (x, y)-coordinates to a NumPy
            # array
            shape = self.camera.predictor(gray, rect)
            shape = face_utils.shape_to_np(shape)



            # extract the left and right eye coordinates, then use the
            # coordinates to compute the eye aspect ratio for both eyes
            leftEye = shape[self.camera.lStart:self.camera.lEnd]
            rightEye = shape[self.camera.rStart:self.camera.rEnd]
            leftEAR = self.camera.eye_aspect_ratio(leftEye)
            rightEAR = self.camera.eye_aspect_ratio(rightEye)

            # average the eye aspect ratio together for both eyes
            ear = (leftEAR + rightEAR) / 2.0

            # compute the convex hull for the left and right eye, then
            # visualize each of the eyes
            leftEyeHull = cv2.convexHull(leftEye)
            rightEyeHull = cv2.convexHull(rightEye)
            cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
            cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)

            # Mouse controls
            face = shape[0:17]
            nose = shape[0:68]
            nose_hull = cv2.convexHull(nose)
            cv2.drawContours(frame, [nose_hull], -1, (0, 255, 0), 1)
            gaze_coordinates = self.camera.gaze_coordinate(
                leftEyeHull , rightEyeHull)
            self.camera.move_mouse_pointer(gaze_coordinates)

            if self.camera.initial_coor is None:
                self.camera.initial_coor = gaze_coordinates
            else:
                if self.camera.within_range(self.camera.initial_coor, gaze_coordinates):
                    self.camera.CLICK_FRAME_COUNTER += 1
                else:
                    self.camera.CLICK_FRAME_COUNTER = 0
                    self.camera.initial_coor = gaze_coordinates
            if self.camera.CLICK_FRAME_COUNTER == self.camera.CLICK_CONSEC_FRAMES:
                self.camera.CLICK_FRAME_COUNTER = 0
                current_pos = [self.camera.root.query_pointer()._data["root_x"], self.camera.root.query_pointer()._data["root_y"]]
                self.camera.mouse.click(current_pos[0], current_pos[1], 1)

                print("Click")

            # Draw gaze
            gaze = np.matrix([gaze_coordinates])
            gaze_hull = cv2.convexHull(gaze.astype(np.int32))


            cv2.drawContours(frame, [gaze_hull], -1, (255, 255, 0), 5)

            # Draw range
            line = np.matrix([[self.camera.X_RANGE[0], self.camera.Y_RANGE[0]],
                              [self.camera.X_RANGE[1], self.camera.Y_RANGE[0]],
                              [self.camera.X_RANGE[1], self.camera.Y_RANGE[1]],
                              [self.camera.X_RANGE[0], self.camera.Y_RANGE[1]]])
            line_hull = cv2.convexHull(line.astype(np.int32))
            cv2.drawContours(frame, [line_hull], -1, (255, 255, 0), 1)

            # check to see if the eye aspect ratio is below the blink
            # threshold, and if so, increment the blink frame counter
            if ear < self.camera.EYE_AR_THRESH:
                self.camera.COUNTER += 1

            # otherwise, the eye aspect ratio is not below the blink
            # threshold
            else:
                # if the eyes were closed for a sufficient number of
                # then increment the total number of blinks
                if self.camera.COUNTER >= self.camera.EYE_AR_CONSEC_FRAMES or key == ord("q"):
                    self.camera.TOTAL += 1
                    self.camera.X_RANGE = [
                        int(face.item(0, 0) + 10), int(face.item(16, 0) - 10)]
                    self.camera.Y_RANGE = [
                        int(face.item(0, 1) - 50), int(face.item(0, 1) + 50)]

                # reset the eye frame counter
                self.camera.COUNTER = 0
        if len(rects) == 0 and not alert_on:
            thread.start_new_thread(self.camera.alert, (25, ))
        # show the frame
        cv2.imshow("Frame", frame)
        self.camera.key = cv2.waitKey(1) & 0xFF
    def checkSkypeIncomingMessages(self,dt):
        global skypeobject
        global skypepopup
        try:
            skypepopup.dismiss()
        except NameError:
             pass
        my_file = Path("skype.txt")
        if my_file.is_file() is False:
            incoming_message=skypeobject.getMsgs()[0]
            popup = Popup(title='Gelen Mesaj', content=Label(text=incoming_message.content),
            auto_dismiss=False)
            popup.open()
            text_file_write = open("skype.txt", "a")
            text_file_write.write("{} ".format(incoming_message.id))
            text_file_write.close()
        else:
            text_file_read = open("skype.txt", "r")
            lines = text_file_read.read().split(' ')
            text_file_read.close()
            incoming_message=skypeobject.getMsgs()
            for i in range(len(incoming_message)):
                message_id=incoming_message[i].id
                #print message_id
                message_info=incoming_message[i].content
                #print message_info

                is_same_id_exist=False
                for j in range(len(lines)):
                    if lines[j]==message_id:
                        is_same_id_exist=True
                if is_same_id_exist == False:
                    global skypepopup
                    skypepopup = Popup(title='Gelen Mesaj', content=Label(text=message_info), size_hint=(None, None), size=(400, 400))



                    skypepopup.open()
                    text_file_write = open("skype.txt", "a")
                    text_file_write.write("{} ".format(message_id))
                    text_file_write.close()


    def get_id(self,  instance):
        for id, widget in instance.parent.ids.items():
            if widget.__self__ == instance:
                return id

    def addOptionsButtonsToArray(self):
        global optionsButtons
        optionsButtons = [
            #self.options_container.ids["back_right"],
            self.options_container.ids["deleteletter"],
            self.options_container.ids["deleteword"],
            self.options_container.ids["tellsentence"],
            self.options_container.ids["sendmessage"],
            self.options_container.ids["watchtv"]]
        for i in range(len(optionsButtons)):
            optionsButtons[i].bind(on_press=self.optionsButtonsClickListener)

    def optionsButtonsClickListener(self, button):
        button.background_color = (88.0, 88.0, 88.0)
        if button.text == "Harfi Sil":
            label = self.sentence_container.ids["label_sentence_inside"]
            label_text_temp = label.text
            label_text_temp = label_text_temp.strip()
            label_text_temp = label_text_temp[0:len(label_text_temp)-1]
            label.text = label_text_temp

        elif button.text == "Kelimeyi Sil":
            label = self.sentence_container.ids["label_sentence_inside"]
            label_text_temp = label.text
            label_text_temp = label_text_temp.strip()
            temp_array = label_text_temp.split("  ")
            temp_array = temp_array[0:len(temp_array)-1]
            label_text_temp = ""
            for i in range(len(temp_array)):
                print temp_array[i]
                label_text_temp = label_text_temp+temp_array[i]+"  "
            label.text = label_text_temp
        elif button.text == "Cümleyi Oku"  :
            Clock.schedule_once(self.say_sentence,1/1000)
        elif button.text == "Mesaj Gönder":
            Clock.schedule_once(self.send_message, 1.0 / 25)


    def send_message(self,dt):
        label = self.sentence_container.ids["label_sentence_inside"]
        global skypeobject
        skypeobject.sendMsg(label.text)
        message_id=skypeobject.getMsgs()[0].id
        text_file_write = open("skype.txt", "a")
        text_file_write.write("{} ".format(message_id))
        text_file_write.close()
        label.text=""

    def say_sentence(self,dt):
        label_text=self.sentence_container.ids["label_sentence_inside"].text
        urllib.urlretrieve('https://tts.voicetech.yandex.net/generate?text='+ label_text +'&format=wav&quality=lo&lang=tr-TR&speaker=zahar&emotion=good&key=5fa13d17-2f87-4db5-9b52-7a654ae3e208', "sound.wav")
        os.system("aplay sound.wav")

    def addAlphabetButtonsToArray(self):

        global alphabetButtons
        alphabetButtons = [
            [#self.autocomplete_container.ids["back_btt"],
             self.autocomplete_container.ids["newword"],
             self.autocomplete_container.ids["completeword1"],
             self.autocomplete_container.ids["completeword2"],
             self.autocomplete_container.ids["completeword3"],
             self.autocomplete_container.ids["completeword4"]],
            [self.alphabet_container.ids["btt_A"],
             self.alphabet_container.ids["btt_B"],
             self.alphabet_container.ids["btt_C"],
             self.alphabet_container.ids["btt_C2"],
             self.alphabet_container.ids["btt_D"],
             self.alphabet_container.ids["btt_E"],
             self.alphabet_container.ids["btt_F"],
             self.alphabet_container.ids["btt_G"],
             self.alphabet_container.ids["btt_G2"]],
            [self.alphabet_container.ids["btt_H"],
             self.alphabet_container.ids["btt_I"],
             self.alphabet_container.ids["btt_I2"],
             self.alphabet_container.ids["btt_J"],
             self.alphabet_container.ids["btt_K"],
             self.alphabet_container.ids["btt_L"],
             self.alphabet_container.ids["btt_M"],
             self.alphabet_container.ids["btt_N"],
             self.alphabet_container.ids["btt_O"],
             self.alphabet_container.ids["btt_O2"]],
            [self.alphabet_container.ids["btt_P"],
             self.alphabet_container.ids["btt_R"],
             self.alphabet_container.ids["btt_S"],
             self.alphabet_container.ids["btt_S2"],
             self.alphabet_container.ids["btt_T"],
             self.alphabet_container.ids["btt_U"],
             self.alphabet_container.ids["btt_U2"],
             self.alphabet_container.ids["btt_V"],
             self.alphabet_container.ids["btt_Y"],
             self.alphabet_container.ids["btt_Z"]]
        ]
        for i in range(len(alphabetButtons)):
            for j in range(len(alphabetButtons[i])):
                alphabetButtons[i][j].bind(on_press=self.alphabetButtonsClickListener)

    def alphabetButtonsClickListener(self, button):
        button.background_color = (88.0, 88.0, 88.0)
        # Prediciton selected
        is_new_word=False
        if self.get_id(button).startswith('completeword'): ## to delete last word if completeword button is selected
            label = self.sentence_container.ids["label_sentence_inside"]
            label_text_temp = label.text
            label_text_temp = label_text_temp.strip()
            temp_array = label_text_temp.split("  ")
            temp_array = temp_array[0:len(temp_array)-1]
            label_text_temp = ""
            for i in range(len(temp_array)):
                print temp_array[i]
                label_text_temp = label_text_temp+temp_array[i]+"  "
            label.text = label_text_temp

        if button.text == "Yeni Kelime":
            is_new_word=True
            label = self.sentence_container.ids["label_sentence_inside"]
            global isSpaceClicked
            isSpaceClicked=True
            label_text_temp = label.text
            if len(label_text_temp) > 0:
                if label_text_temp[len(label_text_temp)-1] != " ":
                    label_text_temp = label_text_temp+"  "
                    label.text = label_text_temp




        if is_new_word is False:
            label = self.sentence_container.ids["label_sentence_inside"]
            label_text = label.text
            label.text = label_text+button.text

            # Prediction
            if len(label.text) > 0:
                predictions = self.word.predict(str(label.text).split()[-1])
                for i in range(4):
                    if len(predictions) > i:
                        self.autocomplete_container.ids["completeword{}".format(i+1)].text = predictions[i][0]




    def clearBackground(self):
        for i in range(len(alphabetButtons)):
            for j in range(len(alphabetButtons[i])):
                alphabetButtons[i][j].background_color = (88.0, 88.0, 88.0)
        for i in range(len(optionsButtons)):
            optionsButtons[i].background_color = (88.0, 88.0, 88.0)



class izgaraApp(App):
    def build(self):
        return RootWidget()


if __name__ == "__main__":
    izgaraApp().run()
