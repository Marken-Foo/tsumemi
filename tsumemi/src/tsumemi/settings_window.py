import os
import tkinter as tk

from tkinter import ttk

import tsumemi.src.tsumemi.img_handlers as imghand


CONFIG_PATH = os.path.relpath(r"tsumemi/resources/config.ini")


class SettingsWindow(tk.Toplevel):
    def __init__(self, controller, *args, **kwargs):
        self.controller = controller
        super().__init__(*args, **kwargs)
        
        self.title("Settings")
        
        piece_palette = ttk.LabelFrame(self, text="Piece graphics")
        piece_palette.grid(column=0, row=0, sticky="EW")
        self.svar_pieces = tk.StringVar(value="TEXT")
        rdo_piece_skin = []
        for n, skin in enumerate(imghand.PieceSkin):
            rdo_piece_skin.append(self._add_rdo_pieceskin(piece_palette, skin))
            rdo_piece_skin[-1].grid(column=0, row=n, sticky="W")
        
        # TODO: Board colour picker???
        board_palette = ttk.LabelFrame(self, text="Board appearance")
        board_palette.grid(column=0, row=1, sticky="EW")
        ttk.Label(board_palette, text="Board").grid(column=0, row=0, sticky="W")
        ttk.Label(board_palette, text="Komadai (solid colour)").grid(column=1, row=0, sticky="W")
        self.svar_board = tk.StringVar(value="WHITE")
        self.svar_komadai = tk.StringVar(value="WHITE")
        rdo_board_skin = []
        rdo_komadai_skin = []
        for n, skin in enumerate(imghand.BoardSkin):
            rdo_board_skin.append(self._add_rdo_boardskin(board_palette, skin))
            rdo_board_skin[-1].grid(column=0, row=n+1, sticky="W")
            rdo_komadai_skin.append(self._add_rdo_komadaiskin(board_palette, skin))
            rdo_komadai_skin[-1].grid(column=1, row=n+1, sticky="W")
        
        buttons_frame = ttk.Frame(self)
        buttons_frame.grid(column=0, row=2, sticky="EW")
        btn_okay = ttk.Button(buttons_frame, text="OK", command=self.save_and_quit)
        btn_okay.grid(column=0, row=2)
        btn_apply = ttk.Button(buttons_frame, text="Apply", command=self.save)
        btn_apply.grid(column=1, row=2)
        return
    
    def _add_rdo_boardskin(self, parent, skin):
        return ttk.Radiobutton(parent, text=skin.desc, variable=self.svar_board, value=skin.name)
    
    def _add_rdo_komadaiskin(self, parent, skin):
        return ttk.Radiobutton(parent, text=skin.desc, variable=self.svar_komadai, value=skin.name)
    
    def _add_rdo_pieceskin(self, parent, skin):
        return ttk.Radiobutton(parent, text=skin.desc, variable=self.svar_pieces, value=skin.name)
    
    def save(self):
        self.controller.config["skins"] = {
            "pieces": self.svar_pieces.get(),
            "board": self.svar_board.get(),
            "komadai": self.svar_komadai.get()
        }
        with open(CONFIG_PATH, "w") as f:
            self.controller.config.write(f)
        # tell the board what skins to use
        piece_skin: imghand.PieceSkin = imghand.PieceSkin[self.svar_pieces.get()]
        board_skin: imghand.BoardSkin = imghand.BoardSkin[self.svar_board.get()]
        komadai_skin: imghand.BoardSkin = imghand.BoardSkin[self.svar_komadai.get()]
        skin_settings = imghand.SkinSettings(
            piece_skin, board_skin, komadai_skin
        )
        self.controller.apply_skin_settings(skin_settings)
        return
    
    def save_and_quit(self):
        self.save()
        self.destroy()