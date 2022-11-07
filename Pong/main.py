import matplotlib.pyplot as plt

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import (
    NumericProperty, ReferenceListProperty, ObjectProperty
)
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.config import Config
from kivy.uix.button import Button

from ai import Dqn

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

brain = Dqn(2, 3, 0.9)
player1_action = [0, 10, -10]
last_reward = 0
scores = []

first_update = True
def init():
    global first_update 
    first_update = False

    last_distance = 0 # Ultima distancia que indica a distancia entre a bola e o retangulo
    

class PongPaddle(Widget):
    score = NumericProperty(0)

    def bounce_ball(self, ball):
        if self.collide_widget(ball):
            vx, vy = ball.velocity
            offset = (ball.center_y - self.center_y) / (self.height / 2)
            bounced = Vector(-1 * vx, vy)
            vel = bounced * 1.1
            ball.velocity = vel.x, vel.y + offset


class PongBall(Widget):
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    velocity = ReferenceListProperty(velocity_x, velocity_y)

    def move(self):
        self.pos = Vector(*self.velocity) + self.pos


class PongGame(Widget):
    pFrame = 0
     
    ball = ObjectProperty(None)
    player1 = ObjectProperty(None)
    player2 = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super(PongGame, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self._keyboard.bind(on_key_up=self._on_keyboard_up)

        self.player1_pressed_keys = set()
        self.player2_pressed_keys = set()

        self.player1_pressed_actions = {
            'w': 10,
            's': -10
        }
        
        self.player2_pressed_actions = {
            'up': 10,
            'down': -10
        }
    
    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard.unbind(on_key_up=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        self.player1_pressed_keys.add(keycode[1])
        self.player2_pressed_keys.add(keycode[1])

    def _on_keyboard_up(self, keyboard, keycode):
        self.player1_pressed_keys.remove(keycode[1])
        self.player2_pressed_keys.remove(keycode[1])

    def text_example(self, text):
        print('Frame: %s Key %s' % (self.pFrame, text))
        
    def serve_ball(self, vel=(4, 0)):
        self.ball.center = self.center
        self.ball.velocity = vel        

    def update(self, dt):
        global brain
        global last_reward
        global scores
        global last_distance
        global ball_x
        global ball_y
        
        if first_update:
            init()
        
        xx = self.player1.x - self.ball.x # Distancia x entre o player1 e a bola
        yy = self.player1.y - self.ball.y # Distancia y entre o player1 e a bola
        last_signal = [xx, yy]
        action = brain.update(last_reward, last_signal)
        scores.append(brain.score())
        player1_move = player1_action[action]
        
        if self.player1.top > self.top:
            self.player1.center_y = 500
        elif self.player1.y < self.y:
            self.player1.center_y = 100
            
        self.player1.center_y += player1_move
        
        if self.ball.x < self.x:
            last_reward = -10
        elif self.ball.right > self.width:
            last_reward = +1
        
        # Resolver
        # for key in self.player1_pressed_keys:
        #     try:
        #         if self.player1.top > self.top:
        #             self.player1.center_y = 500
        #         elif self.player1.y < self.y:
        #             self.player1.center_y = 100
                    
        #         self.player1.center_y += self.player1_pressed_actions[key]
        #     except KeyError:
        #         print("Frame: %s Key %s. Omitted" % (self.pFrame, key))
        
        for key in self.player2_pressed_keys:
            try:
                if self.player2.top > self.top:
                    self.player2.center_y = 500
                elif self.player2.y < self.y:
                    self.player2.center_y = 100
                    
                self.player2.center_y += self.player2_pressed_actions[key]
            except KeyError:
                print("Frame: %s Key %s. Omitted" % (self.pFrame, key))
        
        self.pFrame += 1
                
        self.ball.move()

        self.player1.bounce_ball(self.ball)
        self.player2.bounce_ball(self.ball)

        if (self.ball.y < self.y) or (self.ball.top > self.top):
            self.ball.velocity_y *= -1

        if self.ball.x < self.x:
            self.player2.score += 1
            self.serve_ball(vel=(4, 0))
        if self.ball.right > self.width:
            self.player1.score += 1
            self.serve_ball(vel=(-4, 0))

    def on_touch_move(self, touch):
        if touch.x < self.width / 3:
            self.player1.center_y = touch.y
        if touch.x > self.width - self.width / 3:
            self.player2.center_y = touch.y


class PongApp(App):
    def build(self):
        game = PongGame()
        game.serve_ball()
        
        Clock.schedule_interval(game.update, 1.0 / 60.0)
        savebtn = Button(text = 'save', pos = (game.width, 0))
        loadbtn = Button(text = 'load', pos = (2 * game.width, 0))
        savebtn.bind(on_release = self.save)
        loadbtn.bind(on_release = self.load)
        game.add_widget(savebtn)
        game.add_widget(loadbtn)
        
        return game

    def save(self, obj): # save button
        print("saving brain...")
        brain.save()
        plt.plot(scores)
        plt.show()

    def load(self, obj): # load button
        print("loading last saved brain...")
        brain.load()


if __name__ == '__main__':
    PongApp().run()