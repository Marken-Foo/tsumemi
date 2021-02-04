import tkinter as tk

from tkinter import ttk

from board_canvas import BoardSkin, PieceSkin


class SettingsWindow(tk.Toplevel):
    def __init__(self, controller, *args, **kwargs):
        self.controller = controller
        super().__init__(*args, **kwargs)
        
        self.title("Settings")
        
        piece_palette = ttk.LabelFrame(self, text="Piece graphics")
        piece_palette.grid(column=0, row=0, sticky="EW")
        self.svar_pieces = tk.StringVar(value="TEXT")
        rdo_piece_skin = []
        for n, skin in enumerate(PieceSkin):
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
        for n, skin in enumerate(BoardSkin):
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
        with open("config.ini", "w") as configfile:
            self.controller.config.write(configfile)
        # tell the board what skins to use
        self.controller.board.apply_board_skin(BoardSkin[self.svar_board.get()])
        self.controller.board.apply_piece_skin(PieceSkin[self.svar_pieces.get()])
        self.controller.board.apply_komadai_skin(BoardSkin[self.svar_komadai.get()])
        self.controller.display_problem()
        return
    
    def save_and_quit(self):
        self.save()
        self.destroy()