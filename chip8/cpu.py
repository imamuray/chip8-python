# TODO: 各種命令に対応する関数名はあとでわかりやすいものに変える
class Chip8CPU:
    def __init__(self) -> None:
        pass

    def sys_addr(self):
        """
        machine code routine の nnn へジャンプする。
        """
        pass

    def cls(self):
        """
        00E0 - CLS

        ディスプレイをクリアする。
        """
        pass

    def ret(self):
        """
        00EE - RET

        サブルーチンから戻る。プログラムカウンタにスタックの一番上のアドレスをセットし、スタックポインタから1引く。
        """
        pass

    def jp_addr(self):
        """
        1nnn - JP addr

        アドレス nnn にジャンプする。インタプリタはプログラムカウンタを nnn にする。
        """
        pass

    def call_addr(self):
        """
        2nnn - CALL addr

        アドレス nnn のサブルーチンを call する。
        インタプリタはスタックポインタをインクリメントし、それから現在のプログラムカウンタをスタックの一番上に置く。
        さらにプログラムカウンタに nnn をセットする。
        """
        pass

    def skip_eq_byte(self):
        """
        3xkk - SE Vx, byte

        Vx = kk の場合、次の命令をスキップする。
        インタプリタはレジスタ Vx と kk を比較し、2つが等しいならプログラムカウンタを2進める。
        """
        pass

    def skip_neq_byte(self):
        """
        4xkk - SNE Vx, byte

        Vx != kk の場合、次の命令をスキップする。
        インタプリタはレジスタ Vx と kk を比較し、2つが異なるならプログラムカウンタを2進める。
        """
        pass

    def skip_eq(self):
        """
        5xy0 - SE Vx, Vy

        Vx = Vy の場合、次の命令をスキップする。
        インタプリタはレジスタ Vx と Vy を比較し、2つが等しいならプログラムカウンタを2進める。
        """
        pass

    def load_byte(self):
        """
        6xkk - LD Vx, byte

        Vx に kk をセットする。
        """
        pass

    def add_byte(self):
        """
        7xkk - ADD Vx, byte

        Vx に Vx + kk をセットする。
        """
        pass

    def load(self):
        """
        8xy0 - LD Vx, Vy

        Vx に Vy をセットする。
        """
        pass

    def or_op(self):
        """
        8xy1 - OR Vx, Vy

        Vx に Vx OR Vy をセットする。
        """
        pass

    def and_op(self):
        """
        8xy2 - AND Vx, Vy

        Vx に Vx AND Vy をセットする。
        """
        pass

    def xor_op(self):
        """
        8xy3 - XOR Vx, Vy

        Vx に Vx XOR Vy をセットする。
        """
        pass

    def add_op(self):
        """
        8xy4 - ADD Vx, Vy

        Vx に Vx + Vy をセットする。
        結果が8bit(255)より大きい場合は Vf に 1 、それ以外の場合は 0 をセットする。
        Vx には下位8bitのみ保持する。
        """
        pass

    def sub_op(self):
        """
        8xy5 - SUB Vx, Vy

        Vx に Vx - Vy をセットする。
        Vx > Vy の場合は Vf に 1、それ以外の場合は 0 をセットする。
        """
        pass

    def shr_op(self):
        """
        8xy6 - SHR Vx, {, Vy}

        Vx に Vx を右ビットシフトさせた値をセットする。
        Vx の最下位ビットが1だった場合は Vf に 1、それ以外の場合は 0 をセットする。
        """
        pass

    def subn_op(self):
        """
        8xy7 - SUBN Vx, Vy

        Vx に Vy - Vx をセットする。
        Vy > Vx の場合は Vf に 1、それ以外の場合は 0 をセットする。
        """
        pass

    def shl_op(self):
        """
        8xyE - SHL Vx, {, Vy}

        Vx に Vx を左ビットシフトさせた値をセットする。
        Vx の最上位ビットが1だった場合は Vf に 1、それ以外の場合は 0 をセットする。
        """
        pass

    def skip_neq(self):
        """
        9xy0 - SNE Vx, Vy


        Vx != Vy の場合、次の命令をスキップする。
        インタプリタはレジスタ Vx と Vy を比較し、2つが異なるならプログラムカウンタを2進める。
        """
        pass

    def load_i_addr(self):
        """
        Annn - LD I, addr

        I に nnn をセットする。
        """
        pass

    def jump_v0_addr(self):
        """
        Bnnn - JP V0, addr

        nnn + V0 のアドレスにジャンプする。つまり、プログラムカウンタに nnn + V0 をセットする。
        """
        pass

    def rnd(self):
        """
        Cxkk - RND Vx, byte

        Vx に 0-255 の乱数 AND kk をセットする。
        """
        pass

    def drw(self):
        """
        Dxyn - DRW Vx, Vy, nibble

        アドレス I の n バイトのスプライトを (Vx, Vy) に描画する。
        Vf に collision をセットする。

        アドレス I の n バイトのスプライトを読み出し、スプライトとして (Vx, Vy) に描画する。
        スプライトは画面に XOR する。
        このとき、消されたピクセルが一つでもある場合は Vf に 1、それ以外の場合は 0 をセットする。
        スプライトの一部が画面からはみ出る場合は逆方向に折り返す。
        """
        pass

    def skp(self):
        """
        Ex9E - SKP Vx

        Vx が押された場合、次の命令をスキップする。
        キーボードをチェックし、Vx の値のキーが押されていればプログラムカウンタを2進める。
        """
        pass

    def sknp(self):
        """
        ExA1 - SKNP Vx

        Vx が押されていない場合、次の命令をスキップする。
        キーボードをチェックし、Vx の値のキーが押されてなければプログラムカウンタを2進める。
        """
        pass

    def load_vx_dt(self):
        """
        Fx07 - LD Vx, DT

        Vx に delay timer の値 dt をセットする。
        """
        pass

    def load_key(self):
        """
        Fx0A - LD Vx, K

        押されたキーを Vx にセットする。
        キーが入力されるまで全ての実行をストップする。
        キーが押されたらその値を Vx にセットする。
        """

    def load_dt_vx(self):
        """
        Fx15 - LD DT, Vx

        delay timer dt に Vx をセットする。
        """
        pass

    def add_i_vx(self):
        """
        Fx1E - ADD I, Vx

        I に I + Vx をセットする。
        """
        pass

    def load_font_vx(self):
        """
        Fx29 - LD F, Vx

        I に Vx のスプライト(fontset)のアドレスをセットする。
        """
        pass

    def load_b_vx(self):
        """
        Fx33 - LD B, Vx

        アドレス I, I+1, I+2 に Vx の BCD をセットする。
        アドレス I に Vx の下位3桁目の値、I+1 には下位2桁目の値、I+2 には下位1桁目の値をセットする。
        """
        pass

    def push_vs(self):
        """
        Fx55 - LD [I], Vx

        V0 から Vx までの値を I から始まるアドレスにセットする。
        """
        pass

    def pop_vs(self):
        """
        Fx65 - LD Vx, [I]

        アドレス I から読んだ値を V0 から Vx にセットする。
        """
        pass


if __name__ == "__main__":
    print("hello, chip8")
