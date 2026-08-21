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
#define trigPin2 24
#define echoPin2 25

long duration1, duration2, front, left, right;
int DC1 = 13;
int DC2 = 12;
int SPEED = 11;
Servo myservo;
float a = 1.6667;
float b = 110;
float angle;

void setup() {
    Serial.begin(9600);
    
    pinMode(trigPin, OUTPUT);
    pinMode(echoPin, INPUT);
    
    pinMode(trigPin2, OUTPUT);
    pinMode(echoPin2, INPUT);
    
    pinMode(DC1, OUTPUT);
    pinMode(DC2, OUTPUT);
    pinMode(SPEED, OUTPUT);
    
    myservo.attach(9);
    myservo.write(55);
}

void loop() {
    right = getRight();
    left = getLeft();
    
    ultrasonic.DistanceMeasure();
    front = ultrasonic.microsecondsToCentimeters();
    
    if (front <= 30 && front > 0)
    {
        if ((right < 30 && left > 30) || (right <= 30 && left <= 30))
        {
            angle = b - (a * front);
            angle = constrain(angle, 10, 120);
            myservo.write(angle);
            goFront(255);
            delay(550);
            Stop();
            myservo.write(55);
            goFront(100);
        }
        else
        {
            angle = 55 - (a * front);
            angle = constrain(angle, 10, 55);
            myservo.write(angle);
            goFront(255);
            delay(550);
            Stop();
            myservo.write(55);
            goFront(100);
        }
    }
    else
    {
        goFront(100);
    }
}

int getRight()
{
    digitalWrite(trigPin, LOW);  
    delayMicroseconds(2); 
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10); 
    digitalWrite(trigPin, LOW);
    duration2 = pulseIn(echoPin, HIGH, 30000);
    int rightDist = (duration2 / 2) / 29.1;
    return rightDist;
}

int getLeft()
{
    digitalWrite(trigPin2, LOW);  
    delayMicroseconds(2); 
    digitalWrite(trigPin2, HIGH);
    delayMicroseconds(10); 
    digitalWrite(trigPin2, LOW);
    duration1 = pulseIn(echoPin2, HIGH, 30000);
    int leftDist = (duration1 / 2) / 29.1;
    return leftDist;
}

void goFront(int Speed)
{
    digitalWrite(DC1, HIGH);
    digitalWrite(DC2, LOW);
    analogWrite(SPEED, Speed);
}

void Stop()
{
    digitalWrite(DC1, LOW);
    digitalWrite(DC2, LOW);
}



    

