# coding=utf-8
from subprocess import DEVNULL, PIPE, STDOUT, check_output, check_call, CalledProcessError
from utilities import mongolog, command_success, command_error
import os
import re
import datetime
import pprint
import inspect
#import urllib.parse


#Returns two levels nested list
def getifacestat():

    command = ['ifconfig', '-a']

    try:
        output = check_output(command, stderr=PIPE, universal_newlines=True)
    except CalledProcessError as e:
        return command_error(e, command)


    #After this split each list item contains an interface specs
    output = output.split('\n\n')
    #Removing empty line at the end
    del output[-1]


    ifaces = list()
    for iface in output:

        #Splitting interface lines
        iface = iface.splitlines()

        #Getting iface name on first line
        #We need to split first line and reinsert in the same list
        tempvar = iface.pop(0).split(None, maxsplit=1)
        iface.insert(0, tempvar[0])
        iface.insert(1, tempvar[1])

        #We are going to cut out some useless lines with this instructions
        i = 0
        #Using "enumerate" because we need to modify the original list
        for index, value in enumerate(iface):
            #"i" indicates where to stop cutting
            i += 1
            #Removing useless leading and trailing spaces
            iface[index] = iface[index].strip()
            if iface[index].startswith('UP'): break


        #Inserting just a slice of the list
        ifaces.append( iface[:i] )


    return command_success( ifaces )
