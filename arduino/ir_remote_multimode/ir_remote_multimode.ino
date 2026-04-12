
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

  //clear Serial input buffer
  while (Serial.available() > 0) {
    Serial.read();
  }

  //Main loop: waiting for message to send, or exit command, or press to change mode
  while (1){

    //Serial message : read serial input line
    if (Serial.available() > 0) {
      String input = Serial.readStringUntil('\n');
      input.trim(); // Remove any leading/trailing whitespace

      // Expected input format : address|command
      // Will send only NEC protocol, and no repeat count (0)
      int separatorIndex = input.indexOf('|');
      if (separatorIndex > 0) {
        String addressStr = input.substring(0, separatorIndex);
        String commandStr = input.substring(separatorIndex + 1); 
        uint32_t address = strtoul(addressStr.c_str(), NULL, 0); // Convert to unsigned long
        uint32_t command = strtoul(commandStr.c_str(), NULL, 0);
        irsend.sendNEC(address, command, 0);

        Serial.print("Sent Address=[");
        Serial.print(address);
        Serial.print("] Command=[");
        Serial.print(command);
        Serial.println("]");
      } else {
        Serial.println(F("Invalid input format. Use: address|command"));
      }

    }
    


    if (digitalRead(PIN_BUTTON1) == LOW){
      // Black button pressed, exit sender mode
      sMODE = MODE_RECEIVER;
      set_mode();
      //debounce on the cheap
      delay(250);
      return;
    }
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
