"""Optional webcam capture; frames remain local and are never stored."""
class WebcamController:
    def __init__(self, index=0): self.index=index; self.capture=None; self.hands=None; self.cv2=None; self.error=None
    @property
    def enabled(self): return self.capture is not None
    def enable(self):
        if self.enabled: return True
        try:
            import cv2
            import mediapipe as mp
            self.cv2=cv2
            self.capture=cv2.VideoCapture(self.index)
            if not self.capture.isOpened(): raise RuntimeError("Camera is unavailable or permission was denied")
            self.hands=mp.solutions.hands.Hands(max_num_hands=1,min_detection_confidence=.65,min_tracking_confidence=.55)
            self.error=None; return True
        except Exception as exc:
            self.error=str(exc); self.disable(); return False
    def read_gesture(self):
        if not self.enabled: return "none"
        ok,frame=self.capture.read()
        if not ok: self.error="Could not read a frame from the camera"; return "none"
        rgb=self.cv2.cvtColor(frame,self.cv2.COLOR_BGR2RGB)
        result=self.hands.process(rgb)
        if not result.multi_hand_landmarks: return "none"
        from hci.gesture_recognition import classify_landmarks
        return classify_landmarks(result.multi_hand_landmarks[0].landmark)
    def disable(self):
        if self.capture is not None:
            try: self.capture.release()
            except Exception: pass
        if self.hands is not None:
            try: self.hands.close()
            except Exception: pass
        self.capture=None; self.hands=None
