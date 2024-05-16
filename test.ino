#include <Adafruit_PN532.h>
#define PN532_SS   (10)
Adafruit_PN532 nfc(PN532_SS);

#define MSG_BUFFER_SIZE  (50)
char msg[MSG_BUFFER_SIZE];

enum { NONE, ISO14443A, EMV };
int lastType = NONE;

int PAN_ID = 0x5A;
int PAN_lenght;
int PAN_start_index;

int ExpDateID1 = 0x5F;
int ExpDateID2 = 0x24;
int ExpDateLenght;
int ExpDateStartIndex;

String PANasString;
String ExpDateAsString;
String PANandExpDate;

String UIDasString;
String SecretAsString;
String UIDandSecret;

bool SentMessage = false;

void setup() {
  //Initialize serial
  Serial.begin(9600);

  nfc.begin();

  //check if we can communicate to the PN532 board
  uint32_t versiondata = nfc.getFirmwareVersion();
  Serial.println(versiondata);
  if (! versiondata) {
    Serial.println("Didn't find PN532 board");
    while (1); // halt
  }

  nfc.setPassiveActivationRetries(1); //else, it will endlessly try to retrieve the tag

  nfc.SAMConfig(); //configure board to read NFC stuff
}

void loop() {

  delay(100);
  
  uint8_t uid[7];  // Buffer to store the returned UID
  uint8_t uidLength; // Length of the UID (4 or 7 bytes depending on ISO14443A card type)
                 
  uint8_t response[255]; // Buffer to store the returned data
  uint8_t responseLength=sizeof(response); // Length of the response buffer  

  uint8_t apduOpenPay2Sys[] = {0x00, /* CLA (Class byte) */
                               0xA4, /* INS (Instruction byte; 0xA4:Select Command; 0xB2:Read Record Command */
                               0x04, /* P1  (Parameter 1 byte; The value and meaning depends on the instruction code [INS]) */ 
                               0x00, /* P2  (Parameter 2 byte; The value and meaning depends on the instruction code [INS]) */ 
                               0x0e, /* Lc  (Number of data bytes send to the card) */
                               /* The Data we send is just 2PAY.SYS.DDF01 ASCII encoded */                      
                               0x32, 0x50, 0x41, 0x59, 0x2e, 0x53, 0x59, 0x53, 0x2e, 0x44, 0x44, 0x46, 0x30, 0x31, /* Data  */
                               0x00  /* Le  (Number of data bytes expected in the response. If Le is 0x00, at maximum 256 bytes are expected) */ };  
  
  uint8_t apduOpenAid[] =     {0x00, /* CLA */
                               0xA4, /* INS */
                               0x04, /* P1  */ 
                               0x00, /* P2  */ 
                               0x07, /* Lc  */
                               /* AID for Master Card */
                               0xA0, 0x00, 0x00, 0x00, 0x04, 0x10, 0x10, /* Data */
                               0x00  /* Le  */ };
                               
  uint8_t apduGetPdol[] =     {0x80, /* CLA */
                               0xA8, /* INS */
                               0x00, /* P1  */ 
                               0x00, /* P2  */ 
                               /* for Master Card */
                               0x02, /* Lc  */
                               0x83, 0x00, /* Data  */
                               /* for Visa it might be the following... */
                               //0x0D, /* Lc  */
                               //0x83, 0x0B, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, /* Data  */                               
                               0x00 /* Le  */ };

                              //Maybee only valid for Master Cards in Apple Pay
  uint8_t apduGetPanExpdate[]={0x00, /* CLA */
                               0xb2, /* INS */
                               0x01, /* P1  */
                               0x14, /* P2  */ 
                               0x00  /* Le  */};
  if(lastType==NONE){

    //Function returns true if any NFC capable object was detected by the reader
    if(nfc.inListPassiveTarget()){
      
      // Opens the Master Card AID (Application Identifier), if function returns false maybe a ISO14443A card was placed, checked in the else if
      if(nfc.inDataExchange(apduOpenAid, sizeof(apduOpenAid), response, &responseLength)){
        
        // setting last type, so reading the card is just done once
        lastType = EMV;

        //printing out what was returned by the card
        Serial.println("EMV placed");
        Serial.println("AID return:");
        nfc.PrintHexChar(response, responseLength);
        Serial.println();

    
        //reading the application data which is containing the PAN (Credit card number) and the expiration date
        nfc.inDataExchange(apduGetPanExpdate, sizeof(apduGetPanExpdate), response, &responseLength);
        
        Serial.println("PanExpdate return:");
        nfc.PrintHexChar(response, responseLength);
        Serial.println();

        //we try to find the position of the PAN and it's length in the response (the PAN is identified by 0x5A and the next byte is the length)
        for (int i = 0; i < sizeof(response); i++) {
          if (response[i] == PAN_ID) {
            PAN_lenght = response[i+1];
            PAN_start_index = i+2;
            break;
          }
        }       

        //we will write the PAN into a string
        for (int i = PAN_start_index; i < (PAN_start_index + PAN_lenght) ; i++) {
          if (response[i] < 10) {
            PANasString.concat("0");
            PANasString.concat(String(response[i],HEX));
          }
          else {
            PANasString.concat(String(response[i],HEX));
          }          
        }
        //print out the PAN
        Serial.println("PAN: "+PANasString);
        Serial.println();   

        //we try to find the position of the expiration and it's length in the response (the expiration date is identified by 0x5F 0x24 and the next byte is the length)
        for (int i = 0; i < sizeof(response); i++) {
          if (response[i] == ExpDateID1 and response[i+1] == ExpDateID2) {
            ExpDateLenght = response[i+2];
            ExpDateStartIndex = i+3;
            break;
          }
        }        

        //we will write the expiration date into a string
        for (int i = ExpDateStartIndex; i < (ExpDateStartIndex + ExpDateLenght) ; i++) {
          if (response[i] < 10) {
            ExpDateAsString.concat("0");
             ExpDateAsString.concat(String(response[i],HEX));
          }
          else {
            ExpDateAsString.concat(String(response[i],HEX));
          }        
        }
        //print out the expiration date
        Serial.println("ExpDate "+ExpDateAsString);
        Serial.println();

        //combining the PAN and expiration date so we can send it as one message via MQTT
        PANandExpDate = PANasString + " " + ExpDateAsString;

        //deleting the data, maybe just paranoia...
        PANasString = "";
        ExpDateAsString = "";
        

      } 
      //check if we have a ISO14443A card and can read the UID
      else if(nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, &uid[0], &uidLength)){

        // setting last type, so reading the card is just done once
        lastType = ISO14443A;


        //printing out what UID returnd by the card and writing it into a string
        Serial.println("ISO14443A placed");   
        Serial.print("UID Length: ");Serial.print(uidLength, DEC);Serial.println(" bytes");
        Serial.print("UID Value: ");
        for (uint8_t i=0; i < uidLength; i++) 
        {
          Serial.print(" 0x");Serial.print(uid[i], HEX);          
          UIDasString.concat(String(uid[i],HEX));
        }
        Serial.println();

        // i have stored a "secret" on the NFC tags which will be read here and saved to a string
        int8_t success;
        uint8_t data[32];
        for (uint8_t i = 7; i < 15; i++) {
          success = nfc.ntag2xx_ReadPage(i, data);
          if (success) {
            for (int k = 0; k < 4; k++) {
            SecretAsString.concat((char)data[k]);
            }
          }
        }
        Serial.print("Secret: "+SecretAsString);

        //combining the UID and secret so we can send it as one message via MQTT
        UIDandSecret = UIDasString + " " + SecretAsString;

        //deleting the data, maybe just paranoia...
        UIDasString = "";
        SecretAsString = ""; 
      }
    }
  }
   
  else {
    //EMV REMOVED?
    if(lastType==EMV){

      //publishing the PAN and expiration date via MQTT
      if (SentMessage == false) {
        SentMessage = true;

        PANandExpDate.toCharArray(msg,MSG_BUFFER_SIZE);
        Serial.print("Publish message: ");
        Serial.println(msg);
        //MQTT code here      
      }

      //when EMV was removed, reset some stuff          
      if(!nfc.inDataExchange(apduGetPanExpdate, sizeof(apduGetPanExpdate), response, &responseLength)){
        Serial.println("EMV Removed");
        lastType = NONE;
        SentMessage = false;
        PANandExpDate = "";
      }
    }
    //ISO14443A REMOVED?
    else if(lastType==ISO14443A){

      //publishing the UID and Secret via MQTT
      if (SentMessage == false) {
        SentMessage = true;

        UIDandSecret.toCharArray(msg,MSG_BUFFER_SIZE);
        Serial.println("");
        Serial.print("Publish message: ");
        Serial.println(msg);   
        //MQTT code here 
      }

      //when ISO14443A was removed, reset some stuff 
      if(!nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, &uid[0], &uidLength)){
        Serial.println("ISO14443A removed");
          lastType = NONE;
          SentMessage = false;
          UIDandSecret = "";
      }
    }
  }
 }