from OpenGL.GL.framebufferobjects import *
from OpenGL.GL import *
from OpenGL.GLU import *
import globals,drawing
from globals.types import Point
import bisect

class UIElementList:
    """
    Very basic implementation of a list of UIElements that can be looked up by position.
    It's using an O(n) algorithm, and I'm sure I can do better once everything's working
    """
    def __init__(self):
        self.items = {}

    def __setitem__(self,item,value):
        self.items[item] = value

    def __delitem__(self,item):
        del self.items[item]

    def __contains__(self,item):
        return item in self.items

    def __str__(self):
        return repr(self)

    def __repr__(self):
        out =  ['UIElementList:']
        for item in self.items:
            out.append('%s:%s - %s(%s)' % (item.absolute.bottom_left,item.absolute.top_right,str(item),item.text if hasattr(item,'text') else 'N/A'))
        return '\n'.join(out)
        
    def Get(self,pos):
        """Return the object at a given absolute position, or None if None exist"""
        match = [-1,None]
        for ui,height in self.items.iteritems():
            if pos in ui and ui.Selectable():
                if height > match[0]:
                    match = [height,ui]
        return match[1]
    
class AbsoluteBounds(object):
    """
    Store the bottom left, top right and size data for a rectangle in screen coordinates. We could 
    ask the parent and compute this each time, but it will be more efficient if we store it and 
    use it directly, and rely on the parent to update its children when things change
    """
    def __init__(self):
        self.bottom_left = None
        self.top_right   = None
        self.size        = None

class UIElement(object):
    def __init__(self,parent,pos,tr):
        self.parent   = parent
        self.absolute = AbsoluteBounds()
        self.on       = True
        self.children = []
        self.parent.AddChild(self)
        self.GetAbsoluteInParent = parent.GetAbsolute
        self.root                = parent.root
        self.level               = parent.level + 1
        self.SetBounds(pos,tr)
        self.enabled             = False

    def SetBounds(self,pos,tr):
        self.absolute.bottom_left = self.GetAbsoluteInParent(pos)
        self.absolute.top_right   = self.GetAbsoluteInParent(tr)
        self.absolute.size        = self.absolute.top_right - self.absolute.bottom_left
        self.bottom_left          = pos
        self.top_right            = tr
        self.size                 = tr - pos

    def UpdatePosition(self):
        self.SetBounds(self.bottom_left,self.top_right)
        for child_element in self.children:
            child_element.UpdatePosition()

    def GetAbsolute(self,p):
        return self.absolute.bottom_left + (self.absolute.size*p)

    def GetRelative(self,p):
        p = p.to_float()
        return (p - self.absolute.bottom_left)/self.absolute.size

    def AddChild(self,element):
        self.children.append(element)

    def RemoveChild(self,element):
        for i,child in enumerate(self.children):
            if child is element:
                break
        else:
            return
        del self.children[i]
                

    def __contains__(self,pos):
        if pos.x < self.absolute.bottom_left.x or pos.x >= self.absolute.top_right.x:
            return False
        if pos.y >= self.absolute.bottom_left.y and pos.y < self.absolute.top_right.y:
            return True
        return False

    def Hover(self):
        pass

    def EndHover(self):
        pass

    def Depress(self,pos):
        """
        Called when you the mouse cursor is over the element and the button is pushed down. If the cursor
        is moved away while the button is still down, and then the cursor is moved back over this element
        still with the button held down, this is called again. 

        Returns the target of a dragging event if any. For example, if we return self, then we indicate 
        that we have begun a drag and want to receive all mousemotion events until that drag is ended.
        """
        return None

    def Undepress(self):
        """
        Called after Depress has been called, either when the button is released while the cursor is still
        over the element (In which case a OnClick is called too), or when the cursor moves off the element 
        (when OnClick is not called)
        """
        pass

    def OnClick(self,pos,button):
        """
        Called when the mouse button is pressed and released over an element (although the cursor may move
        off and return between those two events). Pos is absolute coords
        """
        pass

    def Scroll(self,amount):
        """
        Called with the value of 1 for a scroll up, and -1 for a scroll down event. Other things could call
        this with larger values for a bigger scoll action
        """
        pass

    def MouseMotion(self,pos,rel,handled):
        """
        Called when the mouse is moved over the element. Pos is absolute coords
        """
        pass

    def Selectable(self):
        return self.on

    def Disable(self):
        for child in self.children:
            child.Disable()
        self.enabled = False

    def Enable(self):
        for child in self.children:
            child.Enable()
        self.enabled = True

    def Delete(self):
        self.Disable()
        for child in self.children:
            child.Delete()

    def MakeSelectable(self):
        self.on = True
        for child in self.children:
            child.MakeSelectable()

    def MakeUnselectable(self):
        self.on = False
        for child in self.children:
            child.MakeUnselectable()

    def __hash__(self):
        return hash((self.absolute.bottom_left,self.absolute.top_right,self.level))

class RootElement(UIElement):
    """
    A Root Element has no parent. It represents the top level UI element, and thus its coords are
    screen coords. It handles dispatching mouse movements and events. All of its children and
    grand-children (and so on) can register with it (and only it) for handling mouse actions,
    and those actions get dispatched
    """
    def __init__(self,bl,tr):
        self.absolute            = AbsoluteBounds()
        self.on                  = True
        self.GetAbsoluteInParent = lambda x:x
        self.root                = self
        self.level               = 0
        self.hovered             = None
        self.children            = []
        self.active_children     = UIElementList()
        self.depressed           = None
        self.SetBounds(bl,tr)
        
    def RegisterUIElement(self,element):
        self.active_children[element] = element.level

    def RemoveUIElement(self,element):
        try:
            del self.active_children[element]
        except KeyError:
            pass

    def RemoveAllUIElements(self):
        toremove = [child for child in self.active_children.items]
        for child in toremove:
            child.Delete()
        self.active_children = UIElementList()

    def MouseMotion(self,pos,rel,handled):
        """
        Try to handle mouse motion. If it's over one of our elements, return True to indicate that
        the lower levels should not handle it. Else return false to indicate that they should
        """
        if handled:
            return handled
        hovered = self.active_children.Get(pos)
        #I'm not sure about the logic here. It might be a bit inefficient. Seems to work though
        if hovered:
            hovered.MouseMotion(pos,rel,handled)
        if hovered is not self.hovered:
            if self.hovered != None:
                self.hovered.EndHover()
        if not hovered or not self.depressed or (self.depressed and hovered is self.depressed):
            self.hovered = hovered
            if self.hovered:
                self.hovered.Hover()
            
        return True if hovered else False

    def MouseButtonDown(self,pos,button):
        """
        Handle a mouse click at the given position (screen coords) of the given mouse button.
        Return whether it was handled, and whether it started a drag event
        """
        dragging = None
        if self.hovered:
            if button == 1:
                #If you click and hold on a button, it becomes depressed. If you then move the mouse away, 
                #it becomes undepressed, and you can move the mouse back and depress it again (as long as you
                #keep the mouse button down. You can't move over another button and depress it though, so 
                #we record which button is depressed
                if self.depressed:
                    #Something's got a bit messed up and we must have missed undepressing that last depressed button. Do
                    #that now
                    self.depressed.Undepress()
                self.depressed = self.hovered
                dragging = self.depressed.Depress(pos)
            elif button == 4:
                self.hovered.Scroll(1)
            elif button == 5:
                self.hovered.Scroll(-1)
        return True if self.hovered else False,dragging

    def MouseButtonUp(self,pos,button):
        handled = False
        if button == 1:
            if self.hovered and self.hovered is self.depressed:
                self.hovered.OnClick(pos,button)
                handled = True
            if self.depressed:
                #Whatever happens, the button gets depressed
                self.depressed.Undepress()
                self.depressed = None
        
            return handled,False
        return False,False

    def Update(self,t):
        pass
    
    def Draw(self):
        pass

    def KeyUp(self,key):
        pass
    
    def KeyDown(self,key):
        pass

    def CancelMouseMotion(self):
        pass

class UIRoot(RootElement):
    def __init__(self,*args,**kwargs):
        super(UIRoot,self).__init__(*args,**kwargs)
        self.drawable_children = {}
        self.updateable_children = {}

    def Draw(self):
        glDisable(GL_TEXTURE_2D)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_TEXTURE_COORD_ARRAY)
        glLoadIdentity()
        glVertexPointerf(globals.ui_buffer.vertex_data)
        glColorPointer(4,GL_FLOAT,0,globals.ui_buffer.colour_data)
        glDrawElements(GL_QUADS,globals.ui_buffer.current_size,GL_UNSIGNED_INT,globals.ui_buffer.indices)
        glEnable(GL_TEXTURE_2D)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        for item in self.drawable_children:
            item.Draw()

    def Update(self,t):
        #Would it be faster to make a list of items to remove and then remove them, rather than build a new list?
        to_remove = []
        for item in self.updateable_children:
            if item.enabled:
                complete = item.Update(t)
                if complete:
                    to_remove.append(item)
        if len(to_remove) > 0:
            for item in to_remove:
                self.RemoveUpdatable(item)

    def RegisterDrawable(self,item):
        self.drawable_children[item] = True

    def RemoveDrawable(self,item):
        try:
            del self.drawable_children[item]
        except KeyError:
            pass

    def RegisterUpdateable(self,item):
        self.updateable_children[item] = True

    def RemoveUpdatable(self,item):
        try:
            del self.updateable_children[item]
        except KeyError:
            pass
            
class HoverableElement(UIElement):
    """
    This class represents a UI element that accepts a hover; i.e when the cursor is over it the hover event
    does not get passed through to the next layer.
    """
    def __init__(self,parent,pos,tr):
        super(HoverableElement,self).__init__(parent,pos,tr)
        self.root.RegisterUIElement(self)

    def Delete(self):
        self.root.RemoveUIElement(self)
        super(HoverableElement,self).Delete()

    def Disable(self):
        if self.enabled:
            self.root.RemoveUIElement(self)
        super(HoverableElement,self).Disable()

    def Enable(self):
        if not self.enabled:
            self.root.RegisterUIElement(self)
        super(HoverableElement,self).Enable()
    

class Box(UIElement):
    def __init__(self,parent,pos,tr,colour):
        super(Box,self).__init__(parent,pos,tr)
        self.quad = drawing.Quad(globals.ui_buffer)
        self.colour = colour
        self.unselectable_colour = tuple(component*0.6 for component in self.colour)
        self.quad.SetColour(self.colour)
        self.quad.SetVertices(self.absolute.bottom_left,
                              self.absolute.top_right,
                              drawing.constants.DrawLevels.ui)
        self.Enable()

    def UpdatePosition(self):
        super(Box,self).UpdatePosition()
        self.quad.SetVertices(self.absolute.bottom_left,
                              self.absolute.top_right,
                              drawing.constants.DrawLevels.ui)

    def Delete(self):
        super(Box,self).Delete()
        self.quad.Delete()
        
    def Disable(self):
        if self.enabled:
            self.quad.Disable()
        super(Box,self).Disable()
        

    def Enable(self):
        if not self.enabled:
            self.quad.Enable()
        super(Box,self).Enable()

    def SetColour(self,colour):
        self.colour = colour
        self.quad.SetColour(self.colour)

    def MakeSelectable(self):
        super(Box,self).MakeSelectable()
        self.quad.SetColour(self.colour)

    def MakeUnselectable(self):
        super(Box,self).MakeUnselectable()
        self.quad.SetColour(self.unselectable_colour)

class HoverableBox(Box,HoverableElement):
    pass

class TextBox(UIElement):
    """ A Screen-relative text box wraps text to a given size """
    def __init__(self,parent,bl,tr,text,scale,colour = None,textType = drawing.texture.TextTypes.SCREEN_RELATIVE,alignment = drawing.texture.TextAlignments.LEFT):
        if tr == None:
            #If we're given no tr; just set it to one row of text, as wide as it can get without overflowing
            #the parent
            self.shrink_to_fit = True
            text_size          = (globals.text_manager.GetSize(text,scale).to_float()/parent.absolute.size)
            margin             = Point(text_size.y*0.06,text_size.y*0.15)
            tr                 = bl + text_size + margin*2 #Add a little breathing room by using 2.1 instead of 2
            #We'd like to store the margin relative to us, rather than our parent
            self.margin = margin/(tr-bl)
        else:
            self.shrink_to_fit = False
        super(TextBox,self).__init__(parent,bl,tr)
        if not self.shrink_to_fit:
            #In this case our margin is a fixed part of the box
            self.margin      = Point(0.05,0.05)
        self.text        = text
        self.current_enabled = len(self.text)
        self.scale       = scale
        self.colour      = colour
        self.text_type   = textType
        self.alignment   = alignment
        self.text_manager = globals.text_manager
        self.ReallocateResources()
        #self.quads       = [self.text_manager.Letter(char,self.text_type) for char in self.text]
        self.viewpos     = 0
        #that sets the texture coords for us
        self.Position(self.bottom_left,self.scale,self.colour)
        self.Enable()

    def Position(self,pos,scale,colour = None,ignore_height = False):
        """Draw the text at the given location and size. Maybe colour too"""
        #set up the position for the characters. Note that we do everything here in size relative
        #to our text box (so (0,0) is bottom_left, (1,1) is top_right. 
        self.pos = pos
        self.absolute.bottom_left = self.GetAbsoluteInParent(pos)
        self.scale = scale
        self.lowest_y = 0
        row_height = (float(self.text_manager.font_height*self.scale*drawing.texture.global_scale)/self.absolute.size.y)
        #Do this without any kerning or padding for now, and see what it looks like
        cursor = Point(self.margin.x,-self.viewpos + 1 - row_height-self.margin.y)
        letter_sizes = [Point(float(quad.width *self.scale*drawing.texture.global_scale)/self.absolute.size.x,
                              float(quad.height*self.scale*drawing.texture.global_scale)/self.absolute.size.y) for quad in self.quads]
        #for (i,(quad,letter_size)) in enumerate(zip(self.quads,letter_sizes)):
        i = 0
        while i < len(self.quads):
            if i in self.newlines:
                i += 1
                cursor.x = self.margin.x
                cursor.y -= row_height*1.2
                continue
            quad,letter_size = self.quads[i],letter_sizes[i]
            if cursor.x + letter_size.x > (1-self.margin.x)*1.001:
                #This would take us over a line. If we're in the middle of a word, we need to go back to the start of the 
                #word and start the new line there
                restart = False
                if quad.letter in ' \t':
                    #It's whitespace, so ok to start a new line, but do it after the whitespace
                    try:
                        while self.quads[i].letter in ' \t':
                            i += 1
                    except IndexError:
                        break
                    restart = True
                else:
                    #look for the start of the word
                    while i >= 0 and self.quads[i].letter not in ' \t':
                        i -= 1
                    if i <= 0:
                        #This single word is too big for the line. Shit, er, lets just bail
                        break
                    #skip the space
                    i += 1
                    restart = True
                        
                cursor.x = self.margin.x
                cursor.y -= row_height*1.2
                if restart:
                    continue
            
            if cursor.x == self.margin.x and self.alignment == drawing.texture.TextAlignments.CENTRE:
                #If we're at the start of a row, and we're trying to centre the text, then check to see how full this row is
                #and if it's not full, offset so that it becomes centred
                width = 0
                for size in letter_sizes[i:]:
                    width += size.x
                    if width > 1-self.margin.x:
                        width -= size.x
                        break
                if width > 0:
                    cursor.x += float(1-(self.margin.x*2)-width)/2

            target_bl = cursor
            target_tr = target_bl + letter_size
            if target_bl.y < self.lowest_y:
                self.lowest_y = target_bl.y
            if target_bl.y < 0 and not ignore_height:
                #We've gone too far, no more room to write!
                break
            absolute_bl = self.GetAbsolute(target_bl)
            absolute_tr = self.GetAbsolute(target_tr)
            self.SetLetterVertices(i,absolute_bl,
                                   absolute_tr,
                                   drawing.texture.TextTypes.LEVELS[self.text_type])
            if colour:
                quad.SetColour(colour)
            cursor.x += letter_size.x
            i += 1
        #For the quads that we're not using right now, set them to display nothing
        for quad in self.quads[i:]:
            quad.SetVertices(Point(0,0),Point(0,0),-10)
        height = max([q.height for q in self.quads])
        super(TextBox,self).UpdatePosition()

    def SetLetterVertices(self,index,bl,tr,textType):
        self.quads[index].SetVertices(bl,tr,textType)

    def UpdatePosition(self):
        """Called by the parent to tell us we need to recalculate our absolute position"""
        super(TextBox,self).UpdatePosition()
        self.Position(self.pos,self.scale,self.colour)

    def SetPos(self,pos):
        """Called by the user to update our position directly"""
        self.SetBounds(pos,pos + self.size)
        self.Position(pos,self.scale,self.colour)

    def SetColour(self,colour):
        self.colour = colour
        for quad in self.quads:
            quad.SetColour(colour)

    def Delete(self):
        """We're done; pack up and go home!"""
        super(TextBox,self).Delete()
        for quad in self.quads:
            quad.Delete()

    def SetText(self,text,colour = None):
        """Update the text"""
        enabled = self.enabled
        self.Delete()
        if enabled:
            self.Enable()
        self.text = text
        if self.shrink_to_fit:
            text_size          = (globals.text_manager.GetSize(text,self.scale).to_float()/self.parent.absolute.size)
            margin             = Point(text_size.y*0.06,text_size.y*0.15)
            tr                 = self.pos + text_size + margin*2
            #We'd like to store the margin relative to us, rather than our parent
            self.margin = margin/(tr-self.pos)
            self.SetBounds(self.pos,tr)
        self.ReallocateResources()
        self.viewpos = 0
        self.Position(self.pos,self.scale,colour)
        #Updating the quads with self.Position re-enables them, so if we're disabled: don't draw
        if not self.enabled:
            for q in self.quads:
                q.Disable()
        self.current_enabled = len(self.quads)
    
    def ReallocateResources(self):
        self.newlines = []
        for i,char in enumerate(self.text):
            if char == '\n':
                self.newlines.append(i)
        self.quads = [self.text_manager.Letter(char,self.text_type) for char in self.text if char != '\n']

    def Disable(self):
        """Don't draw for a while, maybe we'll need you again"""
        if self.enabled:
            for q in self.quads:
                q.Disable()
        super(TextBox,self).Disable()
        

    def Enable(self):
        """Alright, you're back on the team!"""
        if not self.enabled:
            for q in self.quads:
                q.Enable()
        super(TextBox,self).Enable()

    def EnableChars(self,num = None):
        if num == None:
            num = len(self.quads)
        if num < self.current_enabled:
            for quad in self.quads[num:]:
                quad.Disable()
        elif num > self.current_enabled:
            for quad in self.quads[self.current_enabled:num]:
                quad.Enable()
        self.current_enabled = num

class FaderTextBox(TextBox):
    """A Textbox that can be smoothly faded to a different size / colour"""
    def __init__(self,*args,**kwargs):
        super(FaderTextBox,self).__init__(*args,**kwargs)
        self.draw_scale = 1

    def SetLetterVertices(self,index,bl,tr,textType):
        self.quads[index].SetVertices(bl - self.absolute.bottom_left,tr-self.absolute.bottom_left,textType)

    def SetFade(self,start_time,end_time,end_size,end_colour):
        self.start_time = start_time
        self.end_time   = end_time
        self.duration   = end_time - start_time
        self.start_size = 1
        self.end_size   = end_size
        self.size_difference = self.end_size - self.start_size
        self.end_colour = end_colour
        self.draw_scale = 1
        #self.bl = (self.absolute.bottom_left - self.absolute.size*1.5).to_int()
        #self.tr = (self.absolute.top_right + self.absolute.size*1.5).to_int()
        self.colour_delay = 0.4
        #print bl,tr
        self.Enable()

    def Enable(self):
        if not self.enabled:
            self.root.RegisterUIElement(self)
            self.root.RegisterDrawable(self)
            self.root.RegisterUpdateable(self)
        super(FaderTextBox,self).Enable()

    def Disable(self):
        if self.enabled:
            self.root.RemoveUIElement(self)
            self.root.RemoveDrawable(self)
        super(FaderTextBox,self).Disable()


    def Update(self,t):
        if t > self.end_time:
            return True
        if t < self.start_time:
            return False
        partial = float(t-self.start_time)/self.duration
        partial = partial*partial*(3 - 2*partial) #smoothstep
        self.draw_scale = self.start_size + (self.size_difference*partial)
        if partial > self.colour_delay:
            new_colour = self.colour[:3] + (1-((partial-self.colour_delay)/(1-self.colour_delay)),)
            for quad in self.quads:
                quad.SetColour(new_colour)

    def ReallocateResources(self):
        self.quad_buffer = drawing.QuadBuffer(1024)
        self.text_type = drawing.texture.TextTypes.CUSTOM
        self.quads = [self.text_manager.Letter(char,self.text_type,self.quad_buffer) for char in self.text]

    def Draw(self):
        """
        Draw the text 3 times for the wrap-around effect, even though we can only see this once as the map is
        wider than the screen.
        """
        #Fixme, just draw the one of these that's necessary
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, globals.text_manager.atlas.texture.texture)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)

        glLoadIdentity()
        glTranslate(-globals.tiles.viewpos.Get().x,-globals.tiles.viewpos.Get().y,0)
        glTranslate(self.absolute.bottom_left.x,self.absolute.bottom_left.y,0)
        glScale(self.draw_scale,self.draw_scale,1)
        
        glVertexPointerf(self.quad_buffer.vertex_data)
        glTexCoordPointerf(self.quad_buffer.tc_data)
        glColorPointer(4,GL_FLOAT,0,self.quad_buffer.colour_data)

        glDrawElements(GL_QUADS,self.quad_buffer.current_size,GL_UNSIGNED_INT,self.quad_buffer.indices)

        glLoadIdentity()
        glTranslate(-globals.tiles.viewpos.Get().x-globals.tiles.width*globals.tile_dimensions.x,-globals.tiles.viewpos.Get().y,0)
        glTranslate(self.absolute.bottom_left.x,self.absolute.bottom_left.y,0)
        glScale(self.draw_scale,self.draw_scale,1)
        glDrawElements(GL_QUADS,self.quad_buffer.current_size,GL_UNSIGNED_INT,self.quad_buffer.indices)

        glLoadIdentity()
        glTranslate(-globals.tiles.viewpos.Get().x+globals.tiles.width*globals.tile_dimensions.x,-globals.tiles.viewpos.Get().y,0)
        glTranslate(self.absolute.bottom_left.x,self.absolute.bottom_left.y,0)
        glScale(self.draw_scale,self.draw_scale,1)
        glDrawElements(GL_QUADS,self.quad_buffer.current_size,GL_UNSIGNED_INT,self.quad_buffer.indices)
        
        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_TEXTURE_COORD_ARRAY)


class ScrollTextBox(TextBox):
    """A TextBox that can be scrolled to see text that doesn't fit in the box"""
    def __init__(self,*args,**kwargs):
        super(ScrollTextBox,self).__init__(*args,**kwargs)
        self.dragging = None
        self.Enable()

    def Position(self,pos,scale,colour = None):
        super(ScrollTextBox,self).Position(pos,scale,colour,ignore_height = True)

    def Enable(self):
        if not self.enabled:
            self.root.RegisterUIElement(self)
            self.root.RegisterDrawable(self)
        super(ScrollTextBox,self).Enable()

    def Disable(self):
        if self.enabled:
            self.root.RemoveUIElement(self)
            self.root.RemoveDrawable(self)
        super(ScrollTextBox,self).Disable()

    def Depress(self,pos):
        self.dragging = self.viewpos + self.GetRelative(pos).y
        return self

    def ReallocateResources(self):
        self.quad_buffer = drawing.QuadBuffer(1024)
        self.text_type = drawing.texture.TextTypes.CUSTOM
        self.quads = [self.text_manager.Letter(char,self.text_type,self.quad_buffer) for char in self.text]

    def Draw(self):
        glPushAttrib(GL_VIEWPORT_BIT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        bl = self.absolute.bottom_left.to_int()
        tr = self.absolute.top_right.to_int()
        glOrtho(bl.x, tr.x, bl.y, tr.y,-10000,10000)
        glMatrixMode(GL_MODELVIEW)
        glViewport(bl.x, bl.y, tr.x-bl.x, tr.y-bl.y)

        glTranslate(0,-self.viewpos*self.absolute.size.y,0)
        glVertexPointerf(self.quad_buffer.vertex_data)
        glTexCoordPointerf(self.quad_buffer.tc_data)
        glColorPointer(4,GL_FLOAT,0,self.quad_buffer.colour_data)
        glDrawElements(GL_QUADS,self.quad_buffer.current_size,GL_UNSIGNED_INT,self.quad_buffer.indices)
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, globals.screen.x, 0, globals.screen.y,-10000,10000)
        glMatrixMode(GL_MODELVIEW)
        glPopAttrib()

    def Undepress(self):
        self.dragging = None

    def Scroll(self,amount):
        self.viewpos = self.ValidViewpos(self.viewpos - float(amount)/30)

    def ValidViewpos(self,viewpos):
        low_thresh = 0.05
        high_thresh = 1.05
        if viewpos < self.lowest_y - low_thresh:
            viewpos = self.lowest_y - low_thresh
        if viewpos > low_thresh:
            viewpos = low_thresh
        return viewpos
       
    def MouseMotion(self,pos,rel,handled):
        pos = self.GetRelative(pos)
        low_thresh = 0.05
        high_thresh = 1.05
        if self.dragging != None:
            #print pos,'vp:',self.viewpos,(self.dragging - pos).y
            self.viewpos = self.ValidViewpos(self.dragging - pos.y)

            self.dragging = self.viewpos + pos.y
            if self.dragging > high_thresh:
                self.dragging = high_thresh
            if self.dragging < low_thresh:
                self.dragging = low_thresh
            #print 'stb vp:',self.viewpos
            #self.UpdatePosition()

class TextBoxButton(TextBox):
    def __init__(self,parent,text,pos,tr=None,size=0.5,callback = None,line_width=2,colour=None):
        self.callback    = callback
        self.line_width  = line_width
        self.hovered     = False
        self.selected    = False
        self.depressed   = False
        self.enabled     = False
        self.colour      = colour
        super(TextBoxButton,self).__init__(parent,pos,tr,text,size,colour = colour)
        for i in xrange(4):
            self.hover_quads[i].Disable()
        self.registered = False
        self.Enable()
        
    def Position(self,pos,scale,colour = None):
        super(TextBoxButton,self).Position(pos,scale,colour)
        self.SetVertices()

    def UpdatePosition(self):
        super(TextBoxButton,self).UpdatePosition()
        self.SetVertices()

    def SetVertices(self):
        for i in xrange(4):
            self.hover_quads[i].SetColour((1,0,0,1))
        
        #top bar
        self.hover_quads[0].SetVertices(Point(self.absolute.bottom_left.x,self.absolute.top_right.y-self.line_width),
                                        self.absolute.top_right,
                                        drawing.constants.DrawLevels.ui+1)
        #right bar
        self.hover_quads[1].SetVertices(Point(self.absolute.top_right.x-self.line_width,self.absolute.bottom_left.y),
                                        self.absolute.top_right,
                                        drawing.constants.DrawLevels.ui+1)
        
        #bottom bar
        self.hover_quads[2].SetVertices(self.absolute.bottom_left,
                                        Point(self.absolute.top_right.x,self.absolute.bottom_left.y+self.line_width),
                                        drawing.constants.DrawLevels.ui+1)

        #left bar
        self.hover_quads[3].SetVertices(self.absolute.bottom_left,
                                        Point(self.absolute.bottom_left.x+self.line_width,self.absolute.top_right.y),
                                        drawing.constants.DrawLevels.ui+1)
        if not self.enabled:
            for i in xrange(4):
                self.hover_quads[i].Disable()

                                  
    def SetPos(self,pos):
        #FIXME: This is shit. I can't be removing and adding every frame
        reregister = self.enabled
        if reregister:
            self.root.RemoveUIElement(self)
        super(TextBoxButton,self).SetPos(pos)
        self.SetVertices()
        if reregister:
            self.root.RegisterUIElement(self)

    def ReallocateResources(self):
        super(TextBoxButton,self).ReallocateResources()
        self.hover_quads = [drawing.Quad(globals.ui_buffer) for i in xrange(4)]

    def Delete(self):
        super(TextBoxButton,self).Delete()
        for quad in self.hover_quads:
            quad.Delete()
        self.Disable()

    def Hover(self):
        self.hovered = True
        for i in xrange(4):
            self.hover_quads[i].Enable()

    def EndHover(self):
        self.hovered = False
        if not self.hovered and not self.selected:
            for i in xrange(4):
                self.hover_quads[i].Disable()

    def Selected(self):
        self.selected = True
        for i in xrange(4):
            self.hover_quads[i].SetColour((0,0,1,1))
            if self.enabled:
                self.hover_quads[i].Enable()

    def Unselected(self):
        self.selected = False
        for i in xrange(4):
            self.hover_quads[i].SetColour((1,0,0,1))
        if not self.enabled or (not self.hovered and not self.selected):
            for i in xrange(4):
                self.hover_quads[i].Disable()

    def Depress(self,pos):
        self.depressed = True
        for i in xrange(4):
            self.hover_quads[i].SetColour((1,1,0,1))
        return None

    def Undepress(self):
        self.depressed = False
        for i in xrange(4):
            self.hover_quads[i].SetColour((1,0,0,1))

    def Enable(self):
        if not self.enabled:
            self.root.RegisterUIElement(self)
            if self.hovered:
                self.Hover()
            elif self.selected:
                self.Selected()
            elif self.depressed:
                self.Depressed()
        super(TextBoxButton,self).Enable()

    def Disable(self):
        if self.enabled:
            self.root.RemoveUIElement(self)
            for i in xrange(4):
                self.hover_quads[i].Disable()
        super(TextBoxButton,self).Disable()

    def OnClick(self,pos,button):
        if 1 or self.callback != None and button == 1:
            self.callback(pos)

class Slider(UIElement):
    def __init__(self,parent,bl,tr,points,callback):
        super(Slider,self).__init__(parent,bl,tr)
        self.points   = sorted(points,lambda x,y:cmp(x[0],y[0]))
        self.callback = callback
        self.lines    = []
        self.uilevel  = utils.ui_level+1
        self.enabled  = False
        self.clickable_area = UIElement(self,Point(0.05,0),Point(0.95,1))
        line          = drawing.Quad(globals.ui_buffer)
        line_bl       = self.clickable_area.absolute.bottom_left + self.clickable_area.absolute.size*Point(0,0.3)
        line_tr       = line_bl + self.clickable_area.absolute.size*Point(1,0) + Point(0,2)
        line.SetVertices(line_bl,line_tr,self.uilevel)
        line.Disable()
        
        low  = self.points[ 0][0]
        high = self.points[-1][0]
        self.offsets = [float(value - low)/(high-low) if low != high else 0 for value,index in self.points]
        self.lines.append(line)
        self.index    = 0
        self.pointer_quad = drawing.Quad(globals.ui_buffer)
        self.pointer_colour = (1,0,0,1)
        self.lines.append(self.pointer_quad)
        self.pointer_ui = UIElement(self.clickable_area,Point(0,0),Point(0,0))
        self.SetPointer()
        self.pointer_quad.Disable()
        self.dragging = False
        #now do the blips
        for offset in self.offsets:
            line    = drawing.Quad(globals.ui_buffer)
            line_bl = self.clickable_area.absolute.bottom_left + Point(offset,0.3)*self.clickable_area.absolute.size
            line_tr = line_bl + self.clickable_area.absolute.size*Point(0,0.2) + Point(2,0)
            line.SetVertices(line_bl,line_tr,self.uilevel)
            line.Disable()
            self.lines.append(line)

    def SetPointer(self):
        offset = self.offsets[self.index]
        
        pointer_bl = Point(offset,0.3) - (Point(2,10)/self.clickable_area.absolute.size)
        pointer_tr = pointer_bl + (Point(7,14)/self.clickable_area.absolute.size)
        self.pointer_ui.SetBounds(pointer_bl,pointer_tr)
        self.pointer_quad.SetVertices(self.pointer_ui.absolute.bottom_left,self.pointer_ui.absolute.top_right,self.uilevel + 0.1)
        self.pointer_quad.SetColour(self.pointer_colour)

    def Enable(self):
        if not self.enabled:
            self.root.RegisterUIElement(self)
            for line in self.lines:
                line.Enable()
        super(Slider,self).Enable()

    def Disable(self):
        if self.enabled:
            self.root.RemoveUIElement(self)
            for line in self.lines:
                line.Disable()
        super(Slider,self).Disable()

    def Depress(self,pos):
        #if pos in self.pointer_ui:
        self.dragging = True
        self.MouseMotion(pos,Point(0,0),False)
        #    return self
        #else:
        #    return None

    def MouseMotion(self,pos,rel,handled):
        if not self.dragging:
            return #we don't care
        outer_relative_pos = self.GetRelative(pos)
        if outer_relative_pos.x < 0:
            outer_relative_pos.x = 0
        if outer_relative_pos.x > 1:
            outer_relative_pos = 1
        relative_pos = self.GetAbsolute(outer_relative_pos)
        relative_pos = self.clickable_area.GetRelative(relative_pos)
        pointer_bl = Point(relative_pos.x,0.3) - (Point(2,10)/self.clickable_area.absolute.size)
        pointer_tr = pointer_bl + (Point(7,14)/self.clickable_area.absolute.size)
        #This is a bit of a hack to avoid having to do a calculation
        temp_ui = UIElement(self.clickable_area,pointer_bl,pointer_tr)
        self.pointer_quad.SetVertices(temp_ui.absolute.bottom_left,temp_ui.absolute.top_right,self.uilevel + 0.1)
        self.clickable_area.RemoveChild(temp_ui)
        #If there are any eligible choices between the currently selected choice and the mouse cursor, choose 
        #the one closest to the cursor
        #Where is the mouse?
        i = bisect.bisect_right(self.offsets,relative_pos.x)
        if i == len(self.offsets):
            #It's off the right, so choose the last option
            chosen = i - 1
        elif i == 0:
            #It's off the left, so choose the first
            chosen = 0
        else:
            #It's between 2 options, so choose whichevers closest
            if abs(relative_pos.x - self.offsets[i-1]) < abs(relative_pos.x - self.offsets[i]):
                chosen = i-1
            else:
                chosen = i
            
        if chosen != self.index:
            self.index = chosen
            #self.SetPointer()
            self.callback(self.index)

    def Undepress(self):
        self.dragging = False
        self.SetPointer()

    def OnClick(self,pos,button):
        #For now try just changing which is selected
        return
        if pos in self.pointer_ui or self.dragging:
            #It's a click on the pointer, which we ignore
            return
        #If it's a click to the right or left of the pointer, adjust accordingly
        if pos.x > self.pointer_ui.absolute.top_right.x:
            self.index = (self.index + 1) % len(self.points)
        elif pos.x < self.pointer_ui.absolute.bottom_left.x:
            self.index = (self.index + len(self.points) - 1) % len(self.points)
        else:
            return
        self.SetPointer()
        self.callback(self.index)

class ListBox(UIElement):
    def __init__(self,parent,bl,tr,text_size,items):
        super(ListBox,self).__init__(parent,bl,tr)
        self.text_size = text_size
        self.UpdateItems(items)

    def UpdateItems(self,items):
        #This is a massive hack, using hardcoded values, and generally being shit. I'm bored of UI things now
        enabled = self.enabled
        self.Delete()
        if enabled:
            self.Enable()
        self.children = []
        self.items = items
        height = 0.8
        maxx   = 0
        
        for name,value in self.items:
            t = TextBox(parent = self            ,
                        bl    = Point(0.05,height),
                        tr    = None             ,
                        text  = name             ,
                        scale = self.text_size   )
            height -= t.size.y
            if t.top_right.x > maxx:
                maxx = t.top_right.x
            if not self.enabled:
                t.Disable()
        
        last_height = height = 0.8
        for i,(name,value) in enumerate(self.items):
            if i == len(self.items) -1:
                bl = Point(maxx+0.02,0)
                tr = Point(1,last_height)
            else:
                bl = Point(maxx+0.05,height)
                tr = None
            t = TextBox(parent = self           ,
                        bl     = bl             ,
                        tr     = tr             ,
                        text   = '%s' % value   ,
                        scale  = self.text_size )
            if not self.enabled:
                t.Disable()
            last_height = height
            height -= t.size.y
        
        

class TabPage(UIElement):
    """
    A UIElement that is suitable for using as the target for a Tabbed environment. Instantiating this class with a Tabbed
    environment as the parent automatically adds it as a tab
    """
    def __init__(self,parent,bl,tr,name):
        self.name = name
        super(TabPage,self).__init__(parent,bl,tr)

class TabbedArea(UIElement):
    """
    Represents the drawable area in a Tabbed environment. It's necessary to allow TabPages to specify their coordinates from
    (0,0) to (1,1) and still only take up the part of the TabbedEnvironment reserved for TabPages. It doesn't do much, just
    pass things up to its parent TabbedEnvironment
    """
    def AddChild(self,element):
        super(TabbedArea,self).AddChild(element)
        if isinstance(element,TabPage):
            self.parent.AddTabPage(element)
            
class TabbedEnvironment(UIElement):
    """
    An element that has a number of sub-element tabs. To make a tab you just create a TabPage that has tab_area as its parent
    """
    def __init__(self,parent,bl,tr):
        super(TabbedEnvironment,self).__init__(parent,bl,tr)
        self.tab_area = TabbedArea(self,Point(0,0),Point(1,0.9))
        self.buttons = []
        self.pages   = []
        self.current_page = None

    def AddTabPage(self,page):
        #print 'Adding page',page.name,len(self.buttons)
        if len(self.buttons) == 0:
            xpos = 0
        else:
            xpos = self.buttons[-1].top_right.x
        new_button = TextBoxButton(parent   = self           ,
                                   text     = page.name      ,
                                   pos      = Point(xpos,0.9),
                                   tr       = None           ,
                                   size     = 0.2            ,
                                   callback = utils.ExtraArgs(self.OnClick,len(self.buttons)))
        
        self.buttons.append(new_button)
        self.pages.append(page)
        if len(self.pages) == 1:
            page.Enable()
            self.current_page = page
        else:
            page.Disable()

    def OnClick(self,pos,button):
        if self.pages[button] is not self.current_page:
            self.current_page.Disable()
            self.current_page = self.pages[button]
            self.current_page.Enable()

    def Enable(self):
        #Fixme, don't waste time by enabling then disabling the other pages, do some optimisation st
        #they're not enabled at all
        enabled = self.enabled
        super(TabbedEnvironment,self).Enable()
        for page in self.pages:
            if page is not self.current_page:
                page.Disable()
                
