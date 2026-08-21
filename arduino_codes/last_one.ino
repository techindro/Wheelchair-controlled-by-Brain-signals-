#include <Servo.h>
#include "Arduino.h"

class Ultrasonic
{
public:
    Ultrasonic(int pin);
    void DistanceMeasure();
    long microsecondsToCentimeters();
    long microsecondsToInches();
private:
    int _pin;
    long duration;
};

Ultrasonic::Ultrasonic(int pin)
{
    _pin = pin;
}

void Ultrasonic::DistanceMeasure()
{
    pinMode(_pin, OUTPUT);
    digitalWrite(_pin, LOW);
    delayMicroseconds(2);
    digitalWrite(_pin, HIGH);
    delayMicroseconds(5);
    digitalWrite(_pin, LOW);
    pinMode(_pin, INPUT);
    duration = pulseIn(_pin, HIGH);
}

long Ultrasonic::microsecondsToCentimeters()
{
    return duration / 29 / 2;
}

long Ultrasonic::microsecondsToInches()
{
    return duration / 74 / 2;
}

Ultrasonic ultrasonic(7);

#define trigPin 22
#define echoPin 23
#define BUZZER_PIN 8

long duration2, front, right;
int DC1 = 13;
int DC2 = 12;
int SPEED = 11;
Servo myservo;
float a = 1.6667;
float b = 110;
float angle;

// Speed Control Gears (1=Slow, 2=Medium, 3=Fast)
int currentSpeed = 180;

// Safety Watchdog Timer (Auto-stop if communication lost)
unsigned long lastCommandTime = 0;
const unsigned long SAFETY_TIMEOUT_MS = 2000;
bool isMoving = false;

void setup() {
    Serial.begin(9600);   
    myservo.attach(9);
    myservo.write(55);

    pinMode(trigPin, OUTPUT);
    pinMode(echoPin, INPUT);
    pinMode(BUZZER_PIN, OUTPUT);
    digitalWrite(BUZZER_PIN, LOW);
  
    pinMode(DC1, OUTPUT);
    pinMode(DC2, OUTPUT);
    pinMode(SPEED, OUTPUT);
}

void loop() {
    right = getFront();
    ultrasonic.DistanceMeasure();
    front = ultrasonic.microsecondsToCentimeters();
  
    Serial.print("front is ");
    Serial.println(front);
    Serial.print("right is ");
    Serial.println(right);

    // Obstacle Avoidance Safety Trigger
    if (front < 30 && front > 0)
    {
        // Sound warning buzzer
        digitalWrite(BUZZER_PIN, HIGH);

        if (right < 30)
        {
            angle = b - (a * front);
            myservo.write(angle);
            goFront(250);
            delay(750);
            Stop();
            myservo.write(55);
        }
        else
        {
            myservo.write(10);
            goFront(250);
            delay(750);
            Stop();
            myservo.write(55); 
        }
        digitalWrite(BUZZER_PIN, LOW);
    }
    else
    {
        // Process BCI Commands over Serial
        while (Serial.available() > 0) {
            char inByte = Serial.read();
            lastCommandTime = millis();

            switch (inByte) {   
                case 'f': 
                    goFront(currentSpeed);
                    break;
                case 'b': 
                    goBack(currentSpeed);
                    break;
                case 's': 
                    Stop();
                    break;
                case 'r':
                    myservo.write(10);
                    goFront(250);
                    delay(800);
                    Stop();
                    myservo.write(55);
                    break;
                case 'l':
                    myservo.write(110);  
                    goFront(250);
                    delay(800);
                    Stop();
                    myservo.write(55);
                    break;
                // Speed Mode Gears
                case '1':
                    currentSpeed = 120;
                    break;
                case '2':
                    currentSpeed = 180;
                    break;
                case '3':
                    currentSpeed = 255;
                    break;
                default:
                    myservo.write(55);
                    Serial.println("error");
                    break;    
            } 
        }

        // Safety Fail-Safe Watchdog
        if (isMoving && (millis() - lastCommandTime > SAFETY_TIMEOUT_MS)) {
            Stop();
        }
    }
}

int getFront()
{
    digitalWrite(trigPin, LOW);  
    delayMicroseconds(2); 
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10); 
    digitalWrite(trigPin, LOW);
    duration2 = pulseIn(echoPin, HIGH);
    int front1 = (duration2 / 2) / 29.1;
    return front1;
}

void goFront(int Speed)
{
    digitalWrite(DC1, HIGH);
    digitalWrite(DC2, LOW);
    analogWrite(SPEED, Speed);
    isMoving = true;
}

void goBack(int Speed)
{
    digitalWrite(DC1, LOW);
    digitalWrite(DC2, HIGH);
    analogWrite(SPEED, Speed);
    isMoving = true;
}

void Stop()
{
    digitalWrite(DC1, LOW);
    digitalWrite(DC2, LOW);
    isMoving = false;
}
