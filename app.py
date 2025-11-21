# app.py
import time
import numpy as np
import streamlit as st
import serial
import serial.tools.list_ports
from PIL import Image, ImageDraw, ImageFont
from streamlit_drawable_canvas import st_canvas


def get_serial(port, baud=115200):
    """
    Get or open a persistent Serial connection stored in session_state.
    """
    key = f"ser_{port}_{baud}"
    if key not in st.session_state:
        try:
            st.session_state[key] = serial.Serial(port, baudrate=baud, timeout=0.1)
            time.sleep(2)  # give Arduino time to reset after opening port
        except Exception as e:
            st.error(f"Could not open serial port {port}: {e}")
            return None
    return st.session_state[key]

def send_frame(ser, matrix):
    if ser is None or not ser.is_open:
        st.error("Serial not connected. Please connect in the sidebar.")
        return

    matrix = np.array(matrix, dtype=int)
    if matrix.shape != (8, 8):
        raise ValueError("Matrix must be 8x8")

    data = bytearray()
    data.append(0xAA)

    for r in range(8):
        byte = 0
        for c in range(8):
            if matrix[r, c]:
                # horizontal flip to fix mirror issue
                bit_index = 7 - c
                byte |= (1 << bit_index)
        data.append(byte)

    try:
        ser.write(data)
    except Exception as e:
        st.error(f"Error writing to serial: {e}")



def text_to_frames(text, height=8):
    """Convert text into scrolling 8x8 frames without cutting letters."""
    if not text:
        return []

    font = ImageFont.load_default()

    # 1) Measure text at native size
    tmp_img = Image.new("L", (1, 1), 0)
    tmp_draw = ImageDraw.Draw(tmp_img)
    bbox = tmp_draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]

    # 2) Render text at native height
    img = Image.new("L", (w + 8, h), 0)  # +8 padding at the end
    draw = ImageDraw.Draw(img)
    # align using bbox so we don’t accidentally shift it down
    draw.text((0, -bbox[1]), text, fill=255, font=font)

    # 3) Now scale the whole strip down to target height (8px)
    img = img.resize((img.width, height), resample=Image.BILINEAR)

    # 4) Slide 8×8 window horizontally to create frames
    frames = []
    for x in range(0, img.width - 8 + 1):
        crop = img.crop((x, 0, x + 8, height))
        arr = np.array(crop)
        frames.append((arr > 128).astype(int))

    if frames:
        frames.append(frames[-1].copy())  # small pause at the end

    return frames




def matrix_from_checkboxes():
    """
    Render 8x8 checkboxes and return 8x8 matrix (0/1).
    """
    matrix = np.zeros((8, 8), dtype=int)
    for r in range(8):
        cols = st.columns(8)
        for c in range(8):
            key = f"cell_{r}_{c}"
            val = cols[c].checkbox("", key=key)
            matrix[r, c] = 1 if val else 0
    return matrix

def image_to_8x8(img):
    """
    Convert a canvas RGBA image to 8x8 logical matrix.
    White background, dark strokes -> 1s.
    """
    # Convert to grayscale
    img = img.convert("L")

    # Downsample to 8x8
    img = img.resize((8, 8), Image.BILINEAR)

    arr = np.array(img).astype("float32")
    # Normalize 0..255 -> 0..1
    arr = arr / 255.0

    # Darker than 0.7 -> treat as 'ink'
    mat = (arr < 0.7).astype(int)

    return mat


def draw_grid_16():
    """
    A 16x16 clickable grid. Each checkbox is a 'pixel'.
    Returns a 16x16 matrix of 0/1.
    """
    size = 16
    mat = np.zeros((size, size), dtype=int)
    st.write("Draw by clicking on the grid (16×16 resolution):")
    for r in range(size):
        cols = st.columns(size)
        for c in range(size):
            key = f"drawing_{r}_{c}"
            val = cols[c].checkbox("", key=key)
            mat[r, c] = 1 if val else 0
    return mat

def downsample_16_to_8(mat16):
    """
    Compress 16x16 matrix to 8x8 by OR-ing each 2x2 block.
    If any pixel in the block is ON, the 8x8 pixel is ON.
    """
    out = np.zeros((8, 8), dtype=int)
    for r in range(8):
        for c in range(8):
            block = mat16[r*2:(r+1)*2, c*2:(c+1)*2]
            out[r, c] = 1 if block.sum() > 0 else 0
    return out



def main():


    st.set_page_config(page_title="Arduino LED Matrix Controller", layout="centered")

    # -------------------- SESSION STATE INIT --------------------
    if "ser" not in st.session_state:
        st.session_state.ser = None
    if "connected" not in st.session_state:
        st.session_state.connected = False
    if "port" not in st.session_state:
        st.session_state.port = "COM12"  # default port
    if "baud" not in st.session_state:
        st.session_state.baud = 115200
    
    st.sidebar.header("Connection")

    ports = [p.device for p in serial.tools.list_ports.comports()]
    default_port = st.session_state.port

    # Port select box
    if ports:
        port = st.sidebar.selectbox(
            "Serial Port",
            options=ports + ["Manual..."],
            index=ports.index(default_port) if default_port in ports else len(ports)
        )
    else:
        port = "Manual..."

    if port == "Manual...":
        port = st.sidebar.text_input("Enter port manually", value=default_port)

    baud = st.sidebar.selectbox("Baud Rate", [9600, 57600, 115200], index=2)

    # Connection button
    if st.sidebar.button("Connect / Reconnect"):
        # Close old connection if exists
        if st.session_state.ser:
            try:
                if st.session_state.ser.is_open:
                    st.session_state.ser.close()
            except:
                pass

        # Try opening new serial connection
        try:
            ser = serial.Serial(port, baudrate=baud, timeout=0.1)
            st.session_state.ser = ser
            st.session_state.port = port
            st.session_state.baud = baud
            st.session_state.connected = True
            time.sleep(2)  # allow Arduino reboot
            st.sidebar.success(f"Connected to {port}")
        except Exception as e:
            st.session_state.ser = None
            st.session_state.connected = False
            st.sidebar.error(f"Connection failed: {e}")

    ser = st.session_state.ser

    # If not connected, show info & exit
    if not ser or not st.session_state.connected:
        st.info("Click 'Connect / Reconnect' in the sidebar to begin.")
        return
    
    st.title("🧠 Arduino MAX7219 LED Matrix Controller")

    tab1, tab2, tab3 = st.tabs(["📝 Text Mode", "🔳 Click Grid", "✏️ Draw Mode"])

    # -------- TAB 1: TEXT --------
    with tab1:
        st.subheader("Text → Scrolling LED Matrix")
        text = st.text_input("Enter text:", "Hello")
        speed = st.slider("Scroll speed (ms per frame)", 20, 250, 70)

        if st.button("Send Text"):
            frames = text_to_frames(text)
            for frame in frames:
                send_frame(ser, frame)
                time.sleep(speed / 1000)

    # -------- TAB 2: CLICK GRID --------
    with tab2:
        st.subheader("Click grid to toggle LEDs")
        matrix = matrix_from_checkboxes()
        col1, col2 = st.columns(2)

        with col1:
            st.write("8x8 Matrix:")
            st.write(matrix)

        if col2.button("Update Matrix"):
            send_frame(ser, matrix)
            st.success("Matrix updated!")

# -------- TAB 3: DRAW MODE --------
    with tab3:
        st.subheader("Draw → Auto convert to 8×8")
        st.caption("Click and HOLD to draw in the square. The 8×8 grid updates live.")

        # Canvas where you can click-and-drag
        canvas = st_canvas(
            fill_color="rgba(0, 0, 0, 0)",   # no fill, just strokes
            stroke_width=12,
            stroke_color="#000000",          # black ink
            background_color="#FFFFFF",      # white background
            width=256,
            height=256,
            drawing_mode="freedraw",
            key="draw_canvas",
            update_streamlit=True,           # 👈 CRUCIAL: update while drawing
        )

        if canvas.image_data is not None:
            # canvas.image_data is RGBA float array in [0,255]
            img = Image.fromarray(canvas.image_data.astype("uint8"), mode="RGBA")

            mat8 = image_to_8x8(img)

            col1, col2 = st.columns(2)
            with col1:
                st.write("8x8 Output:")
                st.write(mat8)

            with col2:
                if st.button("Send Drawing"):
                    send_frame(ser, mat8)
                    st.success("Drawing sent to LED matrix!")



if __name__ == "__main__":
    main()
