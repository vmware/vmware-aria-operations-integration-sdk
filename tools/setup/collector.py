import sys
import os
import json

def main(argv):
    if len(argv) == 0:
        print("No arguments")
    elif argv[0] in 'collect':
        print("Python collect")
        //collect()
    elif argv[0] in 'test':
        print("Python test")
        test()
    else:
        print(f"Command {argv[0]} not found")


def connect():

def test():
   //ensure that there is communication  somehow

def collect():
    //container statistics
    cpu_percent = psutil.cpu_percent(1))


class Metric:
    def __init__(self, key: str, value, int):
        #TODO finish constructor
        return  {"key": "string","numberValue": 0,"timestamp": -1}

class Property:
   def __init__ (self, key: str, value ):
    #TODO: parse value and check whether is a string or a number
        {
          "key": "string",
          "stringValue": "string",
          "numberValue": 0,
          "timestamp": -1
        }

class Event:
    def __init__(self, criticality: str, message: str, startDate, updateDate, cancelDate, watchWaitCyccle, cancelWaitCycle):
        #TODO constructor
        {
          "criticality": 0,
          "message": "string",
          "faultKey": "string",
          "autoCancel": false,
          "startDate": 0,
          "updateDate": 0,
          "cancelDate": 0,
          "watchWaitCycle": 1,
          "cancelWaitCycle": 3
        }

class Identifier:
    def __init__(self, key: str, value: str, isPartOfUniqueness: bool):
        #TODO constructor

class Object:
    def __init__(self, name: str, adapterKind: str, bojectKind: str, identifiers:[], ):

def object():
    {
  "result": [
    {
      "key": {
      #Object
      },
      "metrics": [
      #Metric
      ],
      "properties": [
      #Property
      ],
      "events": [
      #Event
      ]
    }
  ],
  "relationships": [
    {
      "parent": {
         #Object
      },
      "children": [
        {
          #Object
        }
      ]
    }
  ],
  "notExistingObjects": [
    {
        #Object
    }
  ],
  "errorMessage": "string"
}



if __name__ == '__main__':
    main(sys.argv[1:])
