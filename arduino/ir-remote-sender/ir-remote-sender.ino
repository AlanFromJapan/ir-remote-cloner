// Arduino code for remote: NEC ceiling light (office)
// Start from the code of IRremote library sample 'SimpleSender' and overwrite the whole code with below.

#include <Arduino.h>
#include "PinDefinitionsAndMore.h"
#include <IRremote.hpp>

IRsend irsend;

void setup() { 
	// Nothing to setup  

  //Buttons are on pin 8-9-12
  pinMode(8, INPUT_PULLUP);
  pinMode(9, INPUT_PULLUP);
  pinMode(12, INPUT_PULLUP);

}

void loop() {  
	uint8_t sRepeats = 0;  // Adjust repeat count as needed

  while(1) {
    if (digitalRead(8) == LOW){
      // Sending key: All lights ON = CMD 166 (0xa6) at ADDR 28034 (0x6d82) using protocol: [8] NEC
      irsend.sendNEC(28034, 166, sRepeats);
      delay(1000);  // Wait 2 seconds between commands     
    }
    if (digitalRead(9) == LOW){
      // Sending key: Light Minimal = CMD 188 (0xbc) at ADDR 28034 (0x6d82) using protocol: [8] NEC
      irsend.sendNEC(28034, 188, sRepeats);
      delay(1000);  // Wait 2 seconds between commands    
    }
    if (digitalRead(12) == LOW){
      // Sending key: Lights OFF = CMD 190 (0xbe) at ADDR 28034 (0x6d82) using protocol: [8] NEC
      irsend.sendNEC(28034, 190, sRepeats);
      delay(1000);  // Wait 2 seconds between commands 
    }
  }
/*
	// Sending key: All lights ON = CMD 166 (0xa6) at ADDR 28034 (0x6d82) using protocol: [8] NEC
	irsend.sendNEC(28034, 166, sRepeats);
	delay(2000);  // Wait 2 seconds between commands

	// Sending key: Light Less = CMD 187 (0xbb) at ADDR 28034 (0x6d82) using protocol: [8] NEC
	irsend.sendNEC(28034, 187, sRepeats);
	delay(2000);  // Wait 2 seconds between commands

	// Sending key: Light Minimal = CMD 188 (0xbc) at ADDR 28034 (0x6d82) using protocol: [8] NEC
	irsend.sendNEC(28034, 188, sRepeats);
	delay(2000);  // Wait 2 seconds between commands

	// Sending key: Light More = CMD 186 (0xba) at ADDR 28034 (0x6d82) using protocol: [8] NEC
	irsend.sendNEC(28034, 186, sRepeats);
	delay(2000);  // Wait 2 seconds between commands

	// Sending key: Lights OFF = CMD 190 (0xbe) at ADDR 28034 (0x6d82) using protocol: [8] NEC
	irsend.sendNEC(28034, 190, sRepeats);
	delay(2000);  // Wait 2 seconds between commands
*/
}