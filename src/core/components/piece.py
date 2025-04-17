from __future__ import annotations
from .period import Period
from .rebar import Rebar
import math
from typing import List
from core.setting import STANDARD_LENGTH

class Piece():
    def __init__(self, rebar: Rebar, theoretical: Period):
        self.theoretical: Period = theoretical
        self.rebar: Rebar = rebar
        self.refresh()
           
    def refresh(self) -> 0:
        self.practical: Period = None
        self.domination = None
        
        self.executive: Period = None

        self.shortest_piece_length: float = None
        self.length_upper_bound: float = None
        
        self.bend: Bend = Bend()
    
    def __eq__(self, other: Piece):
        checks = (
            self.theoretical == other.theoretical,
            self.practical == other.practical,
            self.executive == other.executive,
            self.bend == other.bend,
        )
        return all(checks)

    def __str__(self):
        return (
            "Piece:\n"
            f"\t theoretical: {self.theoretical}\n"
            f"\t practical: {self.practical}\n"
            f"\t executive: {self.executive}\n"
            f"\t bend: {self.bend}"
        )

    @staticmethod
    def get_net_length(length: float, overlap_length: float) -> float:
        """returns the net length of rebars according to the length of period and
        the overlap length of the corresponding rebar. 

        Args:
            length (float): length of the period
            overlap_length (float): the length of the overlap

        Returns:
            float: net length of the rebars
        """
        length = round(length,3)
        if length <= STANDARD_LENGTH:
            return length
        else:
            num_of_pieces = math.ceil(round((length - overlap_length)/(STANDARD_LENGTH - overlap_length),3))
            return ((num_of_pieces - 1) * overlap_length) + length
    
    @staticmethod
    def get_shortest_piece_net_length(length: float, overlap_length: float) -> float:
        length = round(length,3)
        if length <= STANDARD_LENGTH:
            return length
        else:
            num_of_pieces = math.ceil(round((length - overlap_length)/(STANDARD_LENGTH - overlap_length),3))
            net_length = Piece.get_net_length(length, overlap_length)
            return net_length - ((num_of_pieces - 1) * STANDARD_LENGTH)
    
    def get_shortest_piece_length(self, by:str) -> float:
        """returns the shortest piece length based on practical period.
        Returns:
            float: the length.
        """
        length = round(getattr(self,by).get_length(),3)
        return Piece.get_shortest_piece_net_length(length, self.rebar.get_overlap_length())
    
    def get_num_of_pieces(self, by: str) -> int:
        length = round(getattr(self, by).get_length(),3)
        if length <= STANDARD_LENGTH:
            return 1
        else:
            overlap_length = self.rebar.get_overlap_length()
            num_of_pieces = math.ceil(round((length - overlap_length)/(STANDARD_LENGTH - overlap_length),3))
            return num_of_pieces
    
    def get_subpieces(self) -> List[Piece]:
        """returns a list of subpieces of the piece

        Returns:
            List[Piece]: list of pieces
        """
        if round(self.executive.get_length(),3) <= STANDARD_LENGTH:
            return [self]
        else: # multiple pieces
            short_piece_side = None
            pieces = []
            if self.bend.end > 0:
                short_piece_side = "end" # short piece at end
            elif self.bend.start > 0:
                short_piece_side = "start"
            else:
                short_piece_side = "end"
            
            # typical rebars shortest_piece_length is None
            if self.shortest_piece_length is None:
                shortest_piece_length = self.get_shortest_piece_length("executive")
            else:
                shortest_piece_length = self.shortest_piece_length
            
            if short_piece_side == "start":
                # build start piece
                end = self.executive.start + shortest_piece_length
                if self.theoretical.start < end:
                    theoretical = Period(self.theoretical.start,end)
                else:
                    theoretical = Period(end,end)
                piece = Piece(rebar = self.rebar, theoretical=theoretical)
                if self.practical.start < end:
                    practical = Period(self.practical.start,end)
                else:
                    practical = Period(end,end)
                piece.practical = practical
                piece.executive = Period(self.executive.start,end)
                piece.bend = Bend(self.bend.start, 0)
                pieces.append(piece)

                # this new end the overlap of the shortest piece will be longer than the standard length
                end = self.executive.start + self.get_shortest_piece_length("executive")

                # middle pieces
                for i in range(self.get_num_of_pieces(by="executive")-2):
                    start = end - self.rebar.get_overlap_length()
                    end = start + STANDARD_LENGTH
                    theoretical = Period(start,end)
                    piece = Piece(rebar=self.rebar, theoretical=theoretical)
                    piece.practical = theoretical
                    piece.executive = theoretical
                    pieces.append(piece)
                
                # build end piece
                start = end - self.rebar.get_overlap_length()
                end = start + STANDARD_LENGTH
                theoretical = Period(start,self.theoretical.end)
                piece = Piece(self.rebar, theoretical)
                piece.practical = Period(start,self.practical.end)
                piece.executive = Period(start,end)
                piece.bend = Bend(0,self.bend.end)
                pieces.append(piece)

            else: # short_piece_side == "end"
                # start piece
                end = self.executive.start + STANDARD_LENGTH
                theoretical = Period(self.theoretical.start, end)
                piece = Piece(self.rebar, theoretical)
                piece.practical = Period(self.practical.start, end)
                piece.executive = Period(self.executive.start, end)
                piece.bend = Bend(self.bend.start, 0)
                pieces.append(piece)
                
                # middle pieces
                Piece.get_num_of_pieces
                for i in range(self.get_num_of_pieces(by="executive")-2):
                    start = end - self.rebar.get_overlap_length()
                    end = start + STANDARD_LENGTH
                    theoretical = Period(start,end)
                    piece = Piece(rebar=self.rebar, theoretical=theoretical)
                    piece.practical = theoretical
                    piece.executive = theoretical
                    piece.bend = Bend(0,0)
                    pieces.append(piece)
                
                # build end piece
                # this new start the overlap of the shortest piece will be longer than the standard length
                start = end - (shortest_piece_length - self.get_shortest_piece_length("executive")) - self.rebar.get_overlap_length()
                end = start + shortest_piece_length
                if self.theoretical.end > start:
                    theoretical = Period(start,self.theoretical.end)
                else:
                    theoretical = Period(start,start)
                if self.practical.end > start:
                    practical = Period(start, self.practical.end)
                else:
                    practical = Period(start,start)
                piece = Piece(self.rebar, theoretical)
                piece.practical = practical
                piece.executive = Period(start,end)
                piece.bend = Bend(0,self.bend.end)
                pieces.append(piece)

            return pieces

class Bend():
    def __init__(self,start=0, end=0):
        self.start = start
        self.end = end
    
    def __str__(self):
        return f"[{self.start}, {self.end}]"
    
    def __eq__(self, other: Bend):
        return self.start == other.start and self.end == other.end
