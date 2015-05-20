# KosBeat.py
# Or: TchaiKosbie, SchostaKosbie, ProKosbiev 
# Christopher Smith + cvsmith + Lecture 1, Recitation A

################################################################################
# Imports
################################################################################

from Tkinter import *
from eventBasedAnimationClass import EventBasedAnimationClass
from ScalePairs import scalePairs
from KeyPairs import keyPairs
import os, pygame.mixer, time, copy

################################################################################
# Main class
################################################################################

class KosBeat(EventBasedAnimationClass):
# Run KosBeat game
    def initAnimation(self):
    # Set values at the start of each animation
        
        # No nodes on the screen at the start
        self.nodeList = []
        self.connectionList = []
        self.undoList = []

        # Setup audio
        # Numbers taken from "A tutorial for sound in PyGame":
        # http://www.pygame.org/wiki/tutorials 
        # pygame.mixer.init(22050,-16,2,2048)
        pygame.mixer.init(22050,-16,2,2048)

        # Default audio settings
        # Keys defined chromatically, starting with C:1, Db:2, D:3,...B:12
        self.key = 1    # C
        self.scale = "KosBeat\nClassic"  # or major, minor, minorPentatonic
        self.activeOctave = 4
        self.beatsPerMinute = 120
        (self.minBPM, self.maxBPM) = (40, 200)
        self.beatsPerSecond = self.beatsPerMinute / 60.0    # 60s per min
        self.beatsPerMeasure = 4
        self.subdivisionsPerBeat = 2
        self.channel = 0
        self.activeDegree = 1

        self.nodeRadius = 12
        self.menuMargin = 40
        
        self.activeType = "Node"

        self.drawRings = False

        # Menu options for menu at top of screen
        self.makeMenuList()

        self.isPlaying = False

        (self.showScaleOption, self.showKeyOption) = (False, False)
        self.showStartScreen = True

        self.infiniteLoop = False
        (self.minLoops, self.maxLoops) = (1, 10)
        self.numberOfLoops = 2
        self.currentNumberOfLoops = 0

    def makeMenuList(self):
    # Return list of menu nodes and players for the top of the screen
        self.menuList = [MenuPlayer(3, "#e74c3c"), MenuPlayer(4, "#2ecc71"), 
                         MenuPlayer(5, "#3498db"), MenuPlayer(0, "#95a5a6"),
                         MenuNode(1, "#e74c3c"), MenuNode(2, "#e67e22"), 
                         MenuNode(3, "#f1c40f"), MenuNode(4, "#2ecc71"),
                         MenuNode(5, "#3498db"), MenuNode(6, "#9b59b6"), 
                         MenuNode(7, "#34495e")]

        # Initially select the first menuNode
        self.menuList[4].isSelected = True
        self.activeColor = self.menuList[4].color

    def isPointInNode(self, x, y):
    # If click is on an existing node, return True
        # Go through list in reverse to select topmost nodes first
        for node in self.nodeList[::-1]:
            # If click is within node's radius
            if self.isPointInRadius(x, y, node.x, node.y, node.r):
                node.isSelected = True
                return True

    @staticmethod
    def getNumberFromPair(pairs, name):
    # Return numerical entry corresponding to given name in list of pairs
        for pair in pairs:
            if pair[0] == name:
                return pair[1]

    @staticmethod
    def getNameFromPair(pairs, number):
    # Return name corresponding to given number in list of pairs
        for pair in pairs:
            if pair[1] == number:
                return pair[0]

    def isPointInMenu(self, x, y):
    # Return True if given point is within the menu
        numberOfOptions = len(self.menuList)
        if ((y < self.menuMargin * 2) and 
            (abs(x-self.width/2) < self.menuMargin * (numberOfOptions+1)/2)):
            return True
        return False

    def isPointInSettings(self, x, y):
    # Return True if given point is within the settings
        return y > self.height - self.menuMargin * 2

    def isPointInRadius(self, x0, y0, x1, y1, r):
    # Return True (x0, y0) is within r of (x1, y1)
        return (abs(x0 - x1) <= r) and (abs(y0 - y1) <= r)

    def clearListSelection(self, itemsList):
    # Set all items in itemsList to unselected
        for item in itemsList:
            item.isSelected = False

    def makeNodeMenuSelection(self, x, y):
    # Select menuNode if click is within menu
        for option in self.menuList:
            if self.isPointInRadius(x, y, option.x, option.y, option.r):
                self.clearListSelection(self.menuList)
                option.isSelected = True
                self.activeColor = option.color
                if type(option) == MenuNode:
                    self.activeType = "Node"
                    self.activeDegree = option.degree
                else:
                    self.activeType = "Player"
                    self.activeOctave = option.octave

    def makeSettingsSelection(self, x, y):
    # Change the setting corresponding to the click
        margin = self.menuMargin
        # Toggle showKeyOption
        if x < margin * 2: self.showKeyOption = not self.showKeyOption
        else: self.showKeyOption = False
        # Toggle showScaleOption
        if margin * 2 < x < margin * 4: 
            self.showScaleOption = not self.showScaleOption
        else: self.showScaleOption = False
        # Move tempoSlider
        if margin * 6.5 <= x <= margin * 15.5:
            self.setTempoSlider(x, y)
        # Move loopSlider
        if margin * 18 <= x <= margin * 22:
            self.setLoopSlider(x, y)
        # Toggle infinite loop
        if margin * 23 <= x <= margin * 25:
            self.infiniteLoop = not self.infiniteLoop
        # Toggle drawRings
        if x > self.width - margin * 2: self.drawRings = not self.drawRings

    def makeSingleConnection(self, player, node):
    # Make single connection between player and node
        for ringIndex in xrange(len(player.ringList)):
                    # If node is within one of the player's rings
                    ringRadius = player.ringList[ringIndex]
                    if (abs(node.x - player.x) < ringRadius and
                        abs(node.y - player.y) < ringRadius):
                        # Create new Connection with sound's properties
                        newConnection = Connection(player.x, player.y, 
                                                   node.x, node.y,
                                                   self.key, self.scale,
                                                   node.degree, player.octave,
                                                   ringIndex, self.channel)
                        self.connectionList += [newConnection]
                        self.channel += 1
                        pygame.mixer.set_num_channels(self.channel + 1)
                        break

    def makeConnections(self):
    # Make connections between nodes and players, allowing players to play nodes
        # Clear existing connection list
        self.connectionList = []
        self.channel = 0
        listLength = len(self.nodeList)
        # Go through every pair of nodes and players in nodeList
        for originalIndex in xrange(listLength):
            for otherIndex in xrange(originalIndex + 1, listLength):
                # If original is a Player and other is a Node
                if (type(self.nodeList[originalIndex]) == Player and
                    type(self.nodeList[otherIndex]) == Node):
                    player = self.nodeList[originalIndex]
                    node = self.nodeList[otherIndex]
                # If original is a Node and other is a Player
                elif (type(self.nodeList[originalIndex]) == Node and
                      type(self.nodeList[otherIndex]) == Player):
                    player = self.nodeList[otherIndex]
                    node = self.nodeList[originalIndex]
                else:
                    # Skip connection for current pair if they are the same type
                    continue
                self.makeSingleConnection(player, node)

    def isPointOnCanvas(self, x, y):
    # Return True if point is on canvas
        return (0 <= x <= self.width) and (0 <= y <= self.height)

    def leftMouseMoved(self, event):
    # Left mouse moved for click and drag
        # Move a selected node if the mouse is within the screen
        (x, y) = (event.x, event.y)

        if (self.isPointOnCanvas(x, y) and (not self.isPointInMenu(x, y)) and 
           (not self.isPointInSettings(x, y)) and 
           (not(self.width-self.menuMargin*2 < x < self.width and
            2 < y < self.menuMargin*2))):
            for node in self.nodeList:
                if node.isSelected:
                    (node.x, node.y) = (x, y)
                    self.makeConnections()
                    self.redrawAll()
        elif self.isPointInSettings(x, y):
            if self.menuMargin * 6.5 <= x <= self.menuMargin * 15.5:
                self.setTempoSlider(x, y)
            elif self.menuMargin * 18 <= x <= self.menuMargin * 22:
                self.setLoopSlider(x, y)

    def selectScaleAtPoint(self, x, y):
    # Set self.scale to scale at point in scale option menu
        if self.menuMargin * 2 < x < self.menuMargin * 4:
            dy = self.height - self.menuMargin * 2 - y
            if dy > 0:
                newScaleIndex = dy / self.menuMargin
                if newScaleIndex < len(scalePairs):
                    self.scale = scalePairs[newScaleIndex][0]
                    self.makeConnections()
                    self.redrawAll()
                else:
                    self.showScaleOption = False
        else:
            self.showScaleOption = False

    def selectKeyAtPoint(self, x, y):
    # Set self.key to key at point in key option menu
        if x < self.menuMargin * 2:
            dy = self.height - self.menuMargin * 2 - y
            if dy > 0:
                newKey = (dy / self.menuMargin) + 1
                if newKey <= len(keyPairs):
                    self.key = newKey
                    self.makeConnections()
                else:
                    self.showKeyOption = False
        else:
            self.showKeyOption = False

    def reinitializeNodes(self):
    # Remake nodeList after rhythm change
        newNodeList = []
        for node in self.nodeList:
            (x, y, r) = (node.x, node.y, node.r)
            if type(node) == Player:
                new = Player(x, y, r, node.octave, node.color,
                                self.beatsPerMeasure * self.subdivisionsPerBeat)
            else:
                # Otherwise, add new node
                new = Node(x, y, r, self.activeDegree, self.activeColor)
            self.nodeList += [new]

    def setLoopSlider(self, x, y):
    # Set self.numberOfLoops and move loopSlider accordingly
        margin = self.menuMargin
        if (self.height - margin - self.nodeRadius < y < 
            self.height - margin + self.nodeRadius):
            self.numberOfLoops = ((x - margin * 18) * 
                                  (self.maxLoops - self.minLoops) /
                                  (margin * 22 - margin * 18) + self.minLoops)
            self.redrawAll()

    def setTempoSlider(self, x, y):
    # Set self.beatsPerMinute and move tempo slider accordingly
        margin = self.menuMargin
        if (self.height - margin - self.nodeRadius < y < 
            self.height - margin + self.nodeRadius):
            self.beatsPerMinute = ((x - margin * 6.5) * 
                                   (self.maxBPM - self.minBPM) /
                                   (margin * 15.5 - margin * 6.5) + self.minBPM)
            self.beatsPerSecond = self.beatsPerMinute / 60.0
            self.makeConnections()
            self.redrawAll()

    def onMousePressed(self, event):
    # Add new node at location mouse pressed or play existing node
        
        if self.isPlaying:
            return None
        if self.showStartScreen:
            return None
        self.clearListSelection(self.nodeList)
        (x, y, r) = (event.x, event.y, self.nodeRadius)
        if self.isPointInMenu(x, y):
            self.showKeyOption = False
            self.showScaleOption = False
            self.makeNodeMenuSelection(x, y)
        # Clear button
        elif (self.width-self.menuMargin*2 < x < self.width and
            2 < y < self.menuMargin*2): 
            self.nodeList = []
            self.makeConnections()
        elif self.isPointInSettings(x, y):
            self.makeSettingsSelection(x, y)
        elif self.showKeyOption:
            self.selectKeyAtPoint(x, y)
        elif self.showScaleOption:
            self.selectScaleAtPoint(x, y)
        
        # Select node if click is on node, otherwise make new one
        else:
            self.showKeyOption = False
            self.showScaleOption = False
            if not self.isPointInNode(x, y):

                # Otherwise, add new Player or Node
                if self.activeType == "Player":
                    new = Player(x, y, r, self.activeOctave, self.activeColor,
                                self.beatsPerMeasure * self.subdivisionsPerBeat)
                else:
                    # Otherwise, add new node
                    new = Node(x, y, r, self.activeDegree, self.activeColor)
                self.nodeList += [new]

                # Make connections between nodes and players
                self.makeConnections()

    def deleteSelectedNode(self):
    # Delete the selected node in nodeList, if one is selected
        for i in xrange(len(self.nodeList)):
            if self.nodeList[i].isSelected:
                self.nodeList.pop(i)
                self.clearListSelection(self.nodeList)
                self.makeConnections()
                break

    def onKeyPressed(self, event):
    # Handle key presses
        # Play/Pause
        if event.keysym == "space":
            if self.showStartScreen:
                self.showStartScreen = False
                return
            if not self.isPlaying:
                self.isPlaying = True
            else:
                self.isPlaying = False

            if self.isPlaying:
                if self.infiniteLoop:
                    text = ("KosBeat - Playing Infinite Loop...Press 'space' to stop.")
                    self.root.wm_title(text)
                else:
                    text = "KosBeat - Playing %s Loops..." % self.numberOfLoops
                    self.root.wm_title(text)
                self.playLoop()

        # Delete
        elif (event.keysym == "BackSpace") or (event.keysym == "Delete"):
            self.deleteSelectedNode()

        # Clear screen
        elif event.char == "c":
            self.nodeList = []
            self.makeConnections()

    def drawItemsInLists(self, *args):
    # Draw items from lists
        for itemsList in args:
            for item in itemsList:
                item.draw(self.canvas)
                # Draw rings if rings are set to display and item is a player
                if (self.drawRings) and type(item) == Player:
                    item.drawRings(self.canvas)

    def drawNodeSelectionMenu(self):
    # Draw Node selection menu along top of screen
        
        menuMargin = self.menuMargin
        # Start left of center
        cx = (self.width / 2) - (len(self.menuList) / 2) * menuMargin
        # Vertical margin
        cy = menuMargin
        # Circle radius
        r = self.nodeRadius

        # Draw menu box
        self.canvas.create_rectangle(cx-menuMargin, cy-menuMargin+2, 
                                    cx+menuMargin*len(self.menuList), 
                                    cy+menuMargin, fill="#ecf0f1")
        # Draw each node option
        for menuNode in self.menuList:
            (menuNode.x, menuNode.y, menuNode.r) = (cx, cy, r)
            menuNode.draw(self.canvas)
            cx += menuMargin

    def drawRingOption(self):
    # Draw ring toggle option in bottom right
        margin = self.menuMargin * 2
        self.canvas.create_rectangle(self.width-margin, self.height-margin,
                                     self.width, self.height, fill="#ecf0f1")
        message = "Hide Rings" if self.drawRings else "Show Rings"
        self.canvas.create_text(self.width-margin/2, self.height-margin/2,
                                text=message, font=("Helvetica", 10, "bold"))

    def drawScaleOption(self):
    # Draw scale selections in bottom left
        margin = self.menuMargin
        message = "Scale:\n%s" % (self.scale)

        self.canvas.create_rectangle(margin*2, self.height-margin*2,
                                     margin*4, self.height, fill="#ecf0f1") 
        self.canvas.create_text(margin*3, self.height-margin, text=message,
                                font=("Helvetica", 10, "bold"))

        if self.showScaleOption:

            y = self.height - margin * 2 - margin/2

            for pair in scalePairs:

                scaleName = pair[0]
                self.canvas.create_rectangle(margin*2, y-margin/2, 
                                             margin*4, y+margin/2,
                                             fill="#ecf0f1")
                self.canvas.create_text(margin*3, y, text=scaleName)
                y -= margin

    def drawKeyOption(self):
    # Draw key selections in bottom left
        margin = self.menuMargin
        message = "Key: %s" % (KosBeat.getNameFromPair(keyPairs, self.key))

        self.canvas.create_rectangle(2, self.height-margin*2,
                                     margin*2, self.height, fill="#ecf0f1")
        self.canvas.create_text(margin, self.height-margin,text=message,
                                font=("Helvetica", 10, "bold"))

        if self.showKeyOption:

            y = self.height - margin * 2 - margin/2
            for pair in keyPairs:
                keyName = pair[0]
                self.canvas.create_rectangle(2, y-margin/2, 
                                             margin*2, y+margin/2,
                                             fill="#ecf0f1")
                self.canvas.create_text(margin, y, text=keyName)
                y -= margin

    def drawLoopSlider(self):
    # Draw loop slider along bottom of screen
        margin = self.menuMargin
        if not self.infiniteLoop: message = "Loops: %s" % (self.numberOfLoops)
        else: message = "Loops: "
        lineY = self.height-margin
        self.canvas.create_rectangle(margin*16, self.height-margin*2,
                                     self.width-margin*2, self.height, 
                                     fill="#ecf0f1")
        self.canvas.create_text(margin*17, self.height-margin, text=message,
                                font=("Helvetica", 10, "bold"))

        lineStart = margin * 18
        lineEnd = margin * 22

        self.canvas.create_text(lineStart, self.height-margin*0.5,  
                            text=self.minLoops, font=("Helvetica", 10, "bold"))
        self.canvas.create_text(lineEnd, self.height-margin*0.5,
                            text=self.maxLoops, font=("Helvetica", 10, "bold"))

        self.canvas.create_line(lineStart, lineY,
                                lineEnd, self.height-margin)
        if not self.infiniteLoop:
            sliderX = (lineStart + (self.numberOfLoops - self.minLoops) * 
                       (lineEnd - lineStart) / (self.maxLoops - self.minLoops))

            self.canvas.create_oval(sliderX-self.nodeRadius, 
                                lineY-self.nodeRadius, sliderX+self.nodeRadius,
                                lineY+self.nodeRadius, fill="#ecf0f1")

    def drawTempoSlider(self):
    # Draw tempo slider along bottom of screen
        margin = self.menuMargin
        message = "Beats Per\nMinute: %i" % (self.beatsPerMinute)
        lineY = self.height-margin
        self.canvas.create_rectangle(margin*4, self.height-margin*2,
                                     margin*16, self.height, fill="#ecf0f1")
        self.canvas.create_text(margin*5.25, self.height-margin, text=message,
                                font=("Helvetica", 10, "bold"))
        
        lineStart = margin * 6.5
        lineEnd = margin * 15.5

        self.canvas.create_text(lineStart, self.height-margin*0.5, 
                            text=self.minBPM, font=("Helvetica", 10, "bold"))
        self.canvas.create_text(lineEnd, self.height-margin*0.5,
                            text=self.maxBPM, font=("Helvetica", 10, "bold"))
        
        self.canvas.create_line(lineStart, lineY,
                                lineEnd, self.height-margin)
        sliderX = (lineStart + (self.beatsPerMinute-self.minBPM) * 
                    (lineEnd - lineStart) / (self.maxBPM - self.minBPM))

        self.canvas.create_oval(sliderX-self.nodeRadius, 
                            lineY-self.nodeRadius, sliderX+self.nodeRadius,
                            lineY+self.nodeRadius, fill="#ecf0f1")

    def drawInfiniteLoopOption(self):
    # Draw checkbox for infinite loop
        margin = self.menuMargin
        if self.infiniteLoop: message = "Disable\nInfinite Loop"
        else: message = "Enable\nInfinite Loop"

        self.canvas.create_text(margin*23.5, self.height-margin,
                                text=message, font= "Helvetica 10 bold")

    def drawSettings(self):
    # Draw settings along bottom of screen
        # Audio:
            # Key
        self.drawKeyOption()
            # Scale type
        self.drawScaleOption()
        # Rhythm:
            # Tempo
        self.drawTempoSlider()
        # Loops:
        self.drawLoopSlider()
        self.drawInfiniteLoopOption()
        #Display:
            # Show rings
        self.drawRingOption()
        pass
    
    def writeTitle(self):
    # Write title
        title = "KosBeat"
        self.canvas.create_text(10, 2, text=title, anchor=NW,
                                fill="#2c3e50", 
                                font=("Helvetica", 64, "bold"))

    def writeOverview(self):
    # Write overview
        text = "A Geometric Music Generator"
        self.canvas.create_text(10, 94, text=text, anchor=NW, fill="#16a085",
                                font=("Helvetica", 36, "italic"))

    def writeInstructions(self):
    # Write instructions
        text = """Squares are players. Circles are notes.
When players and notes are near each other, the players play the notes.
A player plays the notes closest to itself first.
Each player and note combination produces a different sound.

Click on the type of player or note you want at the top of the screen,
then click to place it on the screen. You may drag existing players and notes
and delete selected ones using "Backspace" or "Delete".

Click on settings at the bottom to customize your composition's properties.

When you are ready to hear your composition, press the space bar.
You cannot edit while audio is playing.
Do not click on the screen while audio is playing.
Your loop will stop on its own after the indicated number of loops.
Or, if you enabled infinite looping, you can press the space bar, and 
after completing one more loop, the audio will stop.
"""
        self.canvas.create_text(10, 150, anchor=NW, fill="#2c3e50", text=text,
                                font=("Helvetica", 20))

    def drawStartPrompt(self):
    # Prompt user to press space to begin
        text = "Press the space bar to begin!"
        self.canvas.create_text(self.width/2, self.height-self.menuMargin*1.5, 
                                text=text, fill="#16a085",
                                font=("Helvetica", 36, "italic"))

    def drawStartScreen(self):
    # Draw start screen at beginning of game
        self.writeTitle()
        self.writeOverview()
        self.writeInstructions()
        self.drawStartPrompt()

    def drawClearButton(self):
    # Draw clear button in upper right corner
        text = "Clear Screen"
        self.canvas.create_rectangle(self.width-self.menuMargin*2, 2,
                                     self.width, self.menuMargin*2, 
                                     fill="#ecf0f1")
        self.canvas.create_text(self.width-self.menuMargin, 
                                self.menuMargin,
                                text=text, font=("Helvetica", 9, "bold"))

    def redrawAll(self):
    # Redraw everything on canvas
        if self.showStartScreen:
            self.drawStartScreen()
            return None
        if self.isPlaying:
            if self.infiniteLoop:
                text = "KosBeat - Playing Infinite Loop...Press the space bar to stop."
                self.root.wm_title(text)
            else:
                text = "KosBeat - Playing %s Loops..." % self.numberOfLoops
                self.root.wm_title(text)
            self.playLoop()
        else:
            self.root.wm_title("KosBeat - Editing")
            self.canvas.delete(ALL)
            # Draw Nodes, Players, and Connections
            self.drawItemsInLists(self.nodeList, self.connectionList)
            self.drawNodeSelectionMenu()
            self.drawSettings()
            self.drawClearButton()
    
    def clearPlayedConnections(self):
    # Reset all connections to unplayed
        for connection in self.connectionList: connection.played = False

    def playLoop(self):
    # Play the audio loop on command
        startTime = time.time()

        while self.isPlaying:
            totalTime = time.time() - startTime
            subdivision = int(totalTime * self.beatsPerSecond * 
                              self.subdivisionsPerBeat)

            for connection in self.connectionList:
                if connection.subdivision == subdivision:
                    # Highlight rings
                    connection.play()

            if subdivision == self.beatsPerMeasure * self.subdivisionsPerBeat:
            # When the end of one measure has been reached
                self.currentNumberOfLoops += 1
                if (not self.infiniteLoop and 
                    self.currentNumberOfLoops >= self.numberOfLoops):
                    self.currentNumberOfLoops = 0
                    self.isPlaying = False
                self.clearPlayedConnections()
                break

################################################################################
# Node class
################################################################################

class Node(object):
# Holds node's location and sound info
    def __init__(self, x, y, r, degree, color):
    # Initialize Node object
        # Sound info
        self.degree = degree
                
        # Location info
        (self.x, self.y, self.r) = (x, y, r)

        # Color info
        self.color = color

        self.isSelected = False

    def draw(self, canvas):
    # Draw Node
        # Draw selection circle if selected
        if self.isSelected:
            selectionColor = "light blue"
            canvas.create_oval(self.x-self.r*3/2, self.y-self.r*3/2, 
                                self.x+self.r*3/2, self.y+self.r*3/2,
                                fill=selectionColor)

        (x, y, r, color) = (self.x, self.y, self.r, self.color)
        canvas.create_oval(x-r, y-r, x+r, y+r, fill=color)

class Player(object):
# Player class
    def __init__(self, x, y, r, octave, color, numRings):
    # Initialize Player object
        (self.x, self.y, self.r) = (x, y, r)
        self.octave = octave
        self.color = color
        self.ringList = []
        self.makeRings(numRings)

        self.isSelected = False

    def draw(self, canvas):
    # Draw Player object
        # Draw selection box if selected
        if self.isSelected:
            selectionColor = "light blue"
            canvas.create_rectangle(self.x-self.r*3/2, self.y-self.r*3/2, 
                                    self.x+self.r*3/2, self.y+self.r*3/2,
                                    fill=selectionColor)

        canvas.create_rectangle(self.x-self.r, self.y-self.r, 
                                self.x+self.r, self.y+self.r, 
                                fill=self.color)

    def drawRings(self, canvas):
    # Draw Player's rings
        for r in self.ringList:
           canvas.create_oval(self.x-r, self.y-r, self.x+r, self.y+r)

    def makeRings(self, numRings):
    # Make numRings rings surrounding each player, 1 for each subdivision
        for radius in xrange(1, numRings + 1):
            # Each new radius's size is increased by a factor of 3
            self.ringList += [self.r * radius * 3]

class Connection(object):
# Connection objects play nodes from players
    def __init__(self, x0, y0, x1, y1, 
                 key, scale, degree, octave, subdivision, channel):
    # Initialize connections
        (self.x0, self.y0) = (x0, y0)
        (self.x1, self.y1) = (x1, y1)
        self.key = key
        self.scale = scale
        self.degree = degree
        self.octave = octave
        self.subdivision = subdivision

        self.numericalName = self.getNumericalName()
        self.path = os.path.join("data", self.numericalName + ".wav")
        self.sound = pygame.mixer.Sound(self.path)
        self.channel = pygame.mixer.Channel(channel)

        self.played = False

    def getNumericalName(self):
    # Return note name from its key, scale, degree, and octave
        # Create name
        currentScale = KosBeat.getNumberFromPair(scalePairs, self.scale)
        # Wrap around for shorter scales at higher degrees
        self.degree = self.degree % len(currentScale) - 1
        # Get numerical note from scale
        currentNumber = currentScale[self.degree]
        # Transpose degree to node's key (If key is 1 for C, no shift)
        currentNumber += self.key - 1
        # Wrap around again after transposition
        # 12 is max note number. 12 remains 12, 13 becomes 1, 14 becomes 2, etc.
        if currentNumber > 12: currentNumber %= 12 

        numericalName = str(self.octave) + os.sep + str(currentNumber)

        return numericalName
        
    def draw(self, canvas):
    # Draw Connection
        canvas.create_line(self.x0, self.y0, self.x1, self.y1)

    def play(self):
    # Play Connection's
        if not self.played:
            self.channel.play(self.sound)
        self.played = True

################################################################################
# Menu classes
################################################################################

class MenuNode(object):
# Holds menu node's properties
    def __init__(self, degree, color):
    # Initialize MenuNode    
        self.degree = degree
        self.color = color
        self.isSelected = False

    def draw(self, canvas):
    # Draw MenuNode
        # Draw selection circle if selected
        if self.isSelected:
            selectionColor = "light blue"
            canvas.create_oval(self.x-self.r*3/2, self.y-self.r*3/2, 
                                self.x+self.r*3/2, self.y+self.r*3/2,
                                fill=selectionColor)

        canvas.create_oval(self.x-self.r, self.y-self.r, 
                                self.x+self.r, self.y+self.r, 
                                fill=self.color)

class MenuPlayer(object):
# Holds menu player's properties
    def __init__(self, octave, color):
    # Initialize MenuPlayer object
        self.octave = octave
        self.color = color
        self.isSelected = False

    def draw(self, canvas):
    # Draw MenuNode
        # Draw selection box if selected
        if self.isSelected:
            selectionColor = "light blue"
            canvas.create_rectangle(self.x-self.r*3/2, self.y-self.r*3/2, 
                                    self.x+self.r*3/2, self.y+self.r*3/2,
                                    fill=selectionColor)

        canvas.create_rectangle(self.x-self.r, self.y-self.r, 
                                self.x+self.r, self.y+self.r, 
                                fill=self.color)

KosBeat(1065, 805).run()