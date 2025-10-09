import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from PIL import Image, ImageTk


class ImageTextboxApp:
    def __init__(self, root):
        self.root = root
        self.root.title("画像プレビューアプリケーション")
        self.root.geometry("1170x450")

        # アップロードされた画像のパスを保存
        self.uploaded_images = []

        # メインコンテナ
        self.setup_ui()

    def setup_ui(self):
        # メインコンテンツエリア（パーン分割）
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 左側パネル: コンポーネント（複数階層）
        self.setup_left_panel()

        # 右側パネル: テキストボックス（画像プレビュー）
        self.setup_right_panel()

    def setup_left_panel(self):
        # 左側フレーム
        left_frame = ttk.Frame(self.paned_window, width=220)
        self.paned_window.add(left_frame, weight=1)

        # ラベル
        label = ttk.Label(
            left_frame, text="Image to Textbox", font=("Arial", 10, "bold")
        )
        label.pack(pady=5, anchor=tk.W, padx=5)

        # フォルダ名入力フレーム
        folder_frame = ttk.Frame(left_frame)
        folder_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(folder_frame, text="フォルダ名:").pack(side=tk.LEFT, padx=(0, 5))
        self.folder_name_entry = ttk.Entry(folder_frame, width=25)
        self.folder_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(folder_frame, text="作成", command=self.on_create_folder).pack(
            side=tk.LEFT, padx=(5, 0)
        )

        # モデル名表示フレーム
        model_frame = ttk.Frame(left_frame)
        model_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(model_frame, text="モデル名:").pack(side=tk.LEFT, padx=(0, 5))
        self.model_name_label = ttk.Label(
            model_frame, text="GPT-4", relief=tk.SUNKEN, width=25, anchor=tk.W
        )
        self.model_name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # ファイルアップロードボタン
        upload_frame = ttk.Frame(left_frame)
        upload_frame.pack(fill=tk.BOTH, padx=5, pady=5)

        ttk.Button(
            upload_frame, text="ファイルをアップロード", command=self.on_file_upload
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(upload_frame, text="リセット", command=self.on_reset).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )

        # ファイル名一覧フレーム
        file_list_frame = ttk.LabelFrame(left_frame, text="ファイル名一覧", padding=5)
        file_list_frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)

        # ファイル名一覧用のリストボックス
        list_scrollbar = ttk.Scrollbar(file_list_frame, orient=tk.VERTICAL)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_listbox = tk.Listbox(
            file_list_frame, yscrollcommand=list_scrollbar.set, height=8
        )
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.config(command=self.file_listbox.yview)

        # コントロールボタンフレーム（開始/停止）
        control_frame = ttk.Frame(left_frame)
        control_frame.pack(fill=tk.Y, padx=5, pady=5)

        self.start_button = ttk.Button(
            control_frame, text="開始", width=12, command=self.on_start
        )
        self.start_button.pack(side=tk.LEFT, padx=2)

        self.stop_button = ttk.Button(
            control_frame,
            text="停止",
            width=12,
            command=self.on_stop,
            state=tk.DISABLED,
        )
        self.stop_button.pack(side=tk.LEFT, padx=2)

        # ステータス表示フレーム
        status_frame = ttk.LabelFrame(left_frame, text="ステータス", padding=5)
        status_frame.pack(
            fill=tk.BOTH,
            padx=5,
            pady=5,
            expand=True,
        )
        self.status_display = ttk.Label(
            status_frame, text="準備完了", anchor=tk.W, font=("Arial", 12)
        )
        self.status_display.pack(fill=tk.X)

    def setup_right_panel(self):
        # 右側フレーム
        right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(right_frame, weight=3)

        # ラベル
        label = ttk.Label(
            right_frame,
            text="画像プレビュー（すべての画像）",
            font=("Arial", 10, "bold"),
        )
        label.pack(pady=5, anchor=tk.W, padx=4)

        # 画像プレビューエリア（スクロール可能なキャンバス）
        canvas_frame = ttk.Frame(right_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # スクロールバー
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # キャンバス
        self.image_canvas = tk.Canvas(
            canvas_frame,
            bg="white",
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set,
        )
        self.image_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        v_scrollbar.config(command=self.image_canvas.yview)
        h_scrollbar.config(command=self.image_canvas.xview)

        # キャンバス内にフレームを作成
        self.images_frame = ttk.Frame(self.image_canvas)
        self.canvas_window = self.image_canvas.create_window(
            (0, 0), window=self.images_frame, anchor=tk.NW
        )

        # フレームのサイズが変更されたときにスクロール領域を更新
        self.images_frame.bind("<Configure>", self.on_frame_configure)

        # プレースホルダーラベル
        self.placeholder_label = ttk.Label(
            self.images_frame,
            text="画像ファイルをアップロードしてください",
            font=("Arial", 12),
            anchor=tk.CENTER,
        )
        self.placeholder_label.pack(pady=50)

    def on_frame_configure(self, event=None):
        """キャンバスのスクロール領域を更新"""
        self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))

    def on_create_folder(self):
        folder_name = self.folder_name_entry.get().strip()
        if folder_name:
            self.status_display.config(text=f"フォルダ '{folder_name}' を作成中...")
            # ここで実際のフォルダ作成処理を行う
            try:
                # 例: Path(folder_name).mkdir(exist_ok=True)
                messagebox.showinfo("成功", f"フォルダ '{folder_name}' を作成しました")
                self.status_display.config(text="準備完了")
            except Exception as e:
                messagebox.showerror("エラー", f"フォルダ作成に失敗しました: {e}")
                self.status_display.config(text="エラー")
        else:
            messagebox.showwarning("警告", "フォルダ名を入力してください")

    def on_file_upload(self):
        file_paths = filedialog.askopenfilenames(
            title="ファイルを選択",
            filetypes=[
                ("画像ファイル (JPEG/PNG)", "*.jpg *.jpeg *.png"),
            ],
        )
        if file_paths:
            for file_path in file_paths:
                file_name = Path(file_path).name
                # リストボックスに追加（重複チェック）
                if file_name not in self.file_listbox.get(0, tk.END):
                    self.file_listbox.insert(tk.END, file_name)
                    # 画像パスを保存
                    self.uploaded_images.append(file_path)

            self.status_display.config(
                text=f"{len(file_paths)}個のファイルをアップロードしました"
            )

            # 画像を表示
            self.display_images()

    def on_reset(self):
        """リセットボタンの処理"""
        # ファイルリストをクリア
        self.file_listbox.delete(0, tk.END)
        self.uploaded_images.clear()

        # 画像表示エリアをクリア
        for widget in self.images_frame.winfo_children():
            widget.destroy()

        self.on_frame_configure()

        # プレースホルダーラベルを再表示
        self.placeholder_label = ttk.Label(
            self.images_frame,
            text="画像ファイルをアップロードしてください",
            font=("Arial", 12),
        )
        self.placeholder_label.pack(pady=50)

        self.status_display.config(text="リセット完了")

    def display_images(self):
        """アップロードされた画像をすべて表示（2列レイアウト）"""
        # プレースホルダーを削除
        if hasattr(self, "placeholder_label"):
            self.placeholder_label.destroy()

        # 既存の画像ウィジェットをクリア
        for widget in self.images_frame.winfo_children():
            widget.destroy()

        # 画像参照を保持するリスト（ガベージコレクション防止）
        self.image_references = []

        # 2列レイアウト用の行フレーム
        current_row_frame = None

        # 各画像を表示
        for idx, img_path in enumerate(self.uploaded_images):
            try:
                # 2列ごとに新しい行フレームを作成
                if idx % 2 == 0:
                    current_row_frame = ttk.Frame(self.images_frame)
                    current_row_frame.pack(fill=tk.X, pady=5)

                # 画像を読み込み
                img = Image.open(img_path)

                # サムネイルサイズに縮小（アスペクト比を維持）
                img.thumbnail((325, 325), Image.Resampling.LANCZOS)

                # PhotoImageに変換
                photo = ImageTk.PhotoImage(img)
                self.image_references.append(photo)

                # フレームを作成（2列配置）
                img_container = ttk.Frame(
                    current_row_frame, relief=tk.RIDGE, borderwidth=2
                )
                img_container.pack(side=tk.LEFT, pady=5, padx=5, expand=True)

                # ファイル名ラベル
                name_label = ttk.Label(
                    img_container,
                    text=Path(img_path).name,
                    font=("Arial", 9, "bold"),
                    wraplength=330,
                )
                name_label.pack(pady=5, padx=5)

                # 画像ラベル
                img_label = tk.Label(img_container, image=photo, bg="white")
                img_label.pack(pady=5, padx=5)

            except Exception as e:
                # エラー時は警告を表示
                if idx % 2 == 0:
                    error_row = ttk.Frame(self.images_frame)
                    error_row.pack(fill=tk.X, pady=5)
                    current_row_frame = error_row

                error_label = ttk.Label(
                    current_row_frame,
                    text=f"エラー: {Path(img_path).name} - {str(e)}",
                    foreground="red",
                )
                error_label.pack(side=tk.LEFT, pady=5, padx=5)

    def on_start(self):
        """開始ボタンの処理"""
        if self.file_listbox.size() == 0:
            messagebox.showwarning("警告", "ファイルをアップロードしてください")
            return

        self.status_display.config(text="処理を開始しました")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        # ここで実際の処理を開始
        messagebox.showinfo("開始", "処理を開始しました")

    def on_stop(self):
        """停止ボタンの処理"""
        self.status_display.config(text="処理を停止しました")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

        # ここで実際の処理を停止
        messagebox.showinfo("停止", "処理を停止しました")


def main():
    root = tk.Tk()
    app = ImageTextboxApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
