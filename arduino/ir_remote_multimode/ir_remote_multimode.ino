
#include <Arduino.h>
/*
 * This include defines the actual pin number for pins like IR_RECEIVE_PIN, IR_SEND_PIN for many different boards and architectures
 */
#include "PinDefinitionsAndMore.h"
#include <IRremote.hpp> // include the library

#define PIN_BUTTON1 8 
#define PIN_BUTTON2 9
#define PIN_BUTTON3 12

#define PIN_MODE1   14
#define PIN_MODE2   15
#define PIN_MODE3   16

#define MODE_RECEIVER 0
#define MODE_SENDER   1
uint8_t sMODE = MODE_RECEIVER;


IRsend irsend;


void setup() {
    Serial.begin(115200);

    // Just to know which program is running on my Arduino
    Serial.println(F("START " __FILE__ " from " __DATE__ "\r\nUsing library version " VERSION_IRREMOTE));

    // Start the receiver and if not 3. parameter specified, take LED_BUILTIN pin from the internal boards definition as default feedback LED
    IrReceiver.begin(IR_RECEIVE_PIN, ENABLE_LED_FEEDBACK);

    Serial.print(F("Ready to receive IR signals of protocols: "));
    printActiveIRProtocols(&Serial);
    Serial.println(F("at pin " STR(IR_RECEIVE_PIN)));

    //Set the input pin for the mode butons to use internal pullup
    pinMode(PIN_BUTTON1, INPUT_PULLUP);
    pinMode(PIN_BUTTON2, INPUT_PULLUP);
    pinMode(PIN_BUTTON3, INPUT_PULLUP);

    //set Leds
    sMODE = MODE_RECEIVER;
    set_mode();
}

/**
* Sets the mode pin (LED) color to show
*/
void set_mode(){
  digitalWrite(PIN_MODE1, LOW);
  digitalWrite(PIN_MODE2, LOW);
  digitalWrite(PIN_MODE3, LOW);

  if (sMODE == MODE_RECEIVER){
    digitalWrite(PIN_MODE3, HIGH);
  }
  else {
    digitalWrite(PIN_MODE1, HIGH);
  }
}


/**
* Allow the 2 buttons to send IR codes
*/
void mode_sender (){
	uint8_t sRepeats = 0;  // Adjust repeat count as needed

  if (digitalRead(PIN_BUTTON2) == LOW){
    // Sending key: All lights ON = CMD 166 (0xa6) at ADDR 28034 (0x6d82) using protocol: [8] NEC
    irsend.sendNEC(28034, 166, sRepeats);
    delay(1000);  // Wait 2 seconds between commands     
  }
  if (digitalRead(PIN_BUTTON3) == LOW){
    // Sending key: Lights OFF = CMD 190 (0xbe) at ADDR 28034 (0x6d82) using protocol: [8] NEC
    irsend.sendNEC(28034, 190, sRepeats);
    delay(1000);  // Wait 2 seconds between commands 
  }
}

/**
* Receive code and reply to Serial port
*/
void mode_receiver() {

    if (IrReceiver.decode()) {

        /*
         * Print a summary of received data
         */
        if (IrReceiver.decodedIRData.protocol == UNKNOWN) {
            Serial.println(F("Received noise or an unknown (or not yet enabled) protocol"));
            // We have an unknown protocol here, print extended info
            IrReceiver.printIRResultRawFormatted(&Serial, true);

            IrReceiver.resume(); // Do it here, to preserve raw data for printing with printIRResultRawFormatted()
        } else {
            IrReceiver.resume(); // Early enable receiving of the next IR frame

            Serial.print(IrReceiver.decodedIRData.protocol);
            Serial.print(";");
            Serial.print(IrReceiver.decodedIRData.address);
            Serial.print(";");
            Serial.print(IrReceiver.decodedIRData.command);
            Serial.print(";");
            Serial.print(IrReceiver.decodedIRData.decodedRawData);
            
            Serial.println("");

        }
    }
}

/**
* Main loop
*/
void loop() {
  //switch mode?
  if (digitalRead(PIN_BUTTON1) == LOW){
    // Black button pressed
    if (sMODE == MODE_RECEIVER){
      sMODE = MODE_SENDER;
      set_mode();
    }
    else {
      sMODE = MODE_RECEIVER;
      set_mode();
    }

    //debounce on the cheap
    delay(250);
  }

  if (sMODE == MODE_RECEIVER){
    mode_receiver();
  }
  else {
    mode_sender();
  }

}
