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

#define trigPin1 53
#define echoPin1 51
#define trigPin2 49
#define echoPin2 47

void setup() {
    Serial.begin(9600);
    pinMode(trigPin1, OUTPUT);
    pinMode(echoPin1, INPUT);
    pinMode(trigPin2, OUTPUT);
    pinMode(echoPin2, INPUT);
}

void loop() {
    long duration1, right;
    long duration2, left;
    long RangeInCentimeters;

    digitalWrite(trigPin1, LOW);  
    delayMicroseconds(2); 
    digitalWrite(trigPin1, HIGH);
    delayMicroseconds(10); 
    digitalWrite(trigPin1, LOW);
    duration1 = pulseIn(echoPin1, HIGH);
    right = (duration1 / 2) / 29.1;
    Serial.print("right is  ");
    Serial.println(right);

    digitalWrite(trigPin2, LOW);  
    delayMicroseconds(2); 
    digitalWrite(trigPin2, HIGH);
    delayMicroseconds(10); 
    digitalWrite(trigPin2, LOW);
    duration2 = pulseIn(echoPin2, HIGH);
    left = (duration2 / 2) / 29.1;
    Serial.print("left is  ");
    Serial.println(left);

    ultrasonic.DistanceMeasure();
    RangeInCentimeters = ultrasonic.microsecondsToCentimeters();
    Serial.print("front ");
    Serial.println(RangeInCentimeters);

    delay(500);
}
