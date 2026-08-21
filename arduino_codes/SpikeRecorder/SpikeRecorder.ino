/*
 * EEG Signal Acquisition - SpikeRecorder Interface
 * =================================================
 * Adapted from megazron/eeg-operated-wheelchair (SpikeRecorder.ino)
 * Original code by Stanislav Mircic, https://backyardbrains.com/
 * 
 * This sketch reads raw EEG/EMG analog signals from a Backyard Brains
 * SpikerShield (or any analog sensor on A0) at high speed using
 * timer interrupts, and streams the data over Serial USB.
 *
 * Compatible with:
 *   - Spike Recorder desktop software
 *   - Custom Python scripts (eeg_signal_processor.py)
 *
 * Wiring:
 *   A0 -> EEG/EMG signal input (SpikerShield output)
 *   Pin 5  -> Message impulse output (optional)
 *   Pin 4  -> Red button input (optional event marker)
 *   Pin 7  -> Green button input (optional event marker)
 *   Pin 13 -> Red LED indicator
 *   Pin 8  -> Green LED indicator
 *
 * Sample Rate: 10 kHz / numberOfChannels
 *   1 channel  = 10 kHz
 *   2 channels = 5 kHz
 */

#define EEG_PIN A0                    // Analog input for EEG signal
#define BUFFER_SIZE 100               // Circular buffer size
#define SIZE_OF_COMMAND_BUFFER 30     // Serial command buffer size
#define LENGTH_OF_MESSAGE_IMPULS 100  // Message impulse duration (ms)

// Register bit manipulation macros
#ifndef cbi
#define cbi(sfr, bit) (_SFR_BYTE(sfr) &= ~_BV(bit))
#endif
#ifndef sbi
#define sbi(sfr, bit) (_SFR_BYTE(sfr) |= _BV(bit))
#endif

// ── Circular Buffer ──
int buffersize = BUFFER_SIZE;
int head = 0;
int tail = 0;
byte writeByte;
byte reading[BUFFER_SIZE];
char commandBuffer[SIZE_OF_COMMAND_BUFFER];

// ── Pins ──
int messageImpulsPin = 5;
int messageImpulseTimer = 0;
int redButton = 4;
int greenButton = 7;
int redLED = 13;
int greenLED = 8;
int redButtonReady = 1;
int greenButtonReady = 1;

// ── Debounce ──
long debouncing_time = 15;
volatile unsigned long last_micros;

// ── Configuration ──
// Baud rate: 230400 for Spike Recorder compatibility
int baudRate = 230400;

// Timer interrupt counter: (16*10^6) / (Fs*8) - 1
//   199  -> 10 kHz sampling
//   1999 -> 1 kHz
//   3999 -> 500 Hz
//   7999 -> 250 Hz
int interrupt_Number = 199;

int numberOfChannels = 1;  // 1 channel = 10 kHz, 2 = 5 kHz
int tempSample = 0;
int commandMode = 0;       // When 1, data transmission is paused


void setup() {
    Serial.begin(baudRate);

    // Configure ADC for faster reading
    // Set ADC prescaler to 16 (1 MHz ADC clock for faster conversion)
    cbi(ADCSRA, ADPS2);
    sbi(ADCSRA, ADPS1);
    sbi(ADCSRA, ADPS0);

    // Configure pins
    pinMode(messageImpulsPin, OUTPUT);
    pinMode(redButton, INPUT);
    pinMode(greenButton, INPUT);
    pinMode(redLED, OUTPUT);
    pinMode(greenLED, OUTPUT);

    // Turn on indicator LEDs briefly
    digitalWrite(redLED, HIGH);
    digitalWrite(greenLED, HIGH);
    delay(300);
    digitalWrite(redLED, LOW);
    digitalWrite(greenLED, LOW);

    // ── Setup Timer1 for precise sampling ──
    cli();  // Disable interrupts

    // Reset Timer1
    TCCR1A = 0;
    TCCR1B = 0;
    TCNT1 = 0;

    // Set compare match register for desired sampling rate
    OCR1A = interrupt_Number;

    // Turn on CTC mode (Clear Timer on Compare Match)
    TCCR1B |= (1 << WGM12);

    // Set prescaler to 8
    TCCR1B |= (1 << CS11);

    // Enable timer compare interrupt
    TIMSK1 |= (1 << OCIE1A);

    sei();  // Enable interrupts
}


// ── Timer1 ISR: High-Speed ADC Sampling ──
ISR(TIMER1_COMPA_vect) {
    // Handle message impulse timing
    if (messageImpulseTimer > 0) {
        messageImpulseTimer--;
        if (messageImpulseTimer == 0) {
            digitalWrite(messageImpulsPin, LOW);
        }
    }

    // Sample all enabled channels
    for (int i = 0; i < numberOfChannels; i++) {
        reading[head] = analogRead(EEG_PIN + i) >> 2;
        head++;
        if (head >= buffersize) {
            head = 0;
        }
    }
}


void loop() {
    // ── Stream sampled data over Serial ──
    if (head != tail && !commandMode) {
        // Spike Recorder protocol: MSB marks frame start
        writeByte = cycleRead();

        // Mark first byte of frame with MSB set
        Serial.write(writeByte | 0x80);

        // Send remaining channel bytes
        for (int i = 1; i < numberOfChannels; i++) {
            if (head != tail) {
                writeByte = cycleRead();
                Serial.write(writeByte & 0x7F);
            }
        }
    }

    // ── Handle Serial Commands ──
    if (Serial.available() > 0) {
        commandMode = 1;  // Pause data while processing commands

        int commandIndex = 0;
        while (Serial.available() > 0) {
            char inChar = Serial.read();
            commandBuffer[commandIndex] = inChar;
            commandIndex++;

            if (commandIndex >= SIZE_OF_COMMAND_BUFFER) break;
            delay(1);  // Wait for next byte
        }

        // Parse known commands
        // "conf s:{rate};" - Set sampling rate
        // "conf c:{channels};" - Set channel count
        // "h:{text};" - Send event marker
        if (commandIndex > 4 && commandBuffer[0] == 'c' && commandBuffer[4] == 's') {
            // Parse new sampling rate
            int newRate = 0;
            for (int j = 6; j < commandIndex && commandBuffer[j] != ';'; j++) {
                newRate = newRate * 10 + (commandBuffer[j] - '0');
            }
            if (newRate > 0) {
                interrupt_Number = newRate;
                OCR1A = interrupt_Number;
            }
        }
        else if (commandIndex > 4 && commandBuffer[0] == 'c' && commandBuffer[4] == 'c') {
            // Parse new channel count
            int newChannels = commandBuffer[6] - '0';
            if (newChannels > 0 && newChannels <= 6) {
                numberOfChannels = newChannels;
            }
        }

        commandMode = 0;  // Resume data transmission
    }

    // ── Button Event Markers ──
    // Red button = event marker type 1
    if (digitalRead(redButton) == HIGH && redButtonReady) {
        redButtonReady = 0;
        digitalWrite(messageImpulsPin, HIGH);
        messageImpulseTimer = LENGTH_OF_MESSAGE_IMPULS;
        digitalWrite(redLED, HIGH);
    }
    if (digitalRead(redButton) == LOW && !redButtonReady) {
        redButtonReady = 1;
        digitalWrite(redLED, LOW);
    }

    // Green button = event marker type 2
    if (digitalRead(greenButton) == HIGH && greenButtonReady) {
        greenButtonReady = 0;
        digitalWrite(greenLED, HIGH);
    }
    if (digitalRead(greenButton) == LOW && !greenButtonReady) {
        greenButtonReady = 1;
        digitalWrite(greenLED, LOW);
    }
}


// ── Circular Buffer Read ──
byte cycleRead() {
    byte result = reading[tail];
    tail++;
    if (tail >= buffersize) {
        tail = 0;
    }
    return result;
}
