import lasio
import pandas as pd
import os
import io


class LASHandler:
    """
    Handles loading and parsing of LAS (Log ASCII Standard) files.
    """

    def __init__(self):
        self.las = None
        self.filepath = None

    def load_file(self, file_source):
        """
        Loads a LAS file from a filepath or a file-like object.
        """
        try:
            # lasio.read accepts both strings (paths) and file-like objects
            # If it's a Streamlit UploadedFile, it might need to be read as string or bytes depending on lasio version,
            # but usually passing the object directly works if it has .read()
            # For robust handling with Streamlit UploadedFile (which is bytes-like), we pass it directly.

            # If it's a bytes object (sometimes needed if specific encoding issues), we might decode,
            # but lasio handles standard inputs well.

            if hasattr(file_source, "name"):
                self.filepath = file_source.name  # Use the filename
            else:
                self.filepath = str(file_source)

            # If file_source is a file path (str), read directly
            if isinstance(file_source, str):
                self.las = lasio.read(file_source)
            else:
                # Assuming file-like object (e.g. Streamlit UploadedFile)
                # Reset pointer to start
                if hasattr(file_source, "seek"):
                    file_source.seek(0)

                content = file_source.read()

                # If bytes, decode to string
                if isinstance(content, bytes):
                    # Try common encodings for LAS files
                    try:
                        file_content_str = content.decode("utf-8", errors="replace")
                    except UnicodeDecodeError:
                        file_content_str = content.decode("latin-1")
                else:
                    file_content_str = content

                # Use StringIO to pass as text stream
                self.las = lasio.read(io.StringIO(file_content_str))

            return True, "File loaded successfully."
        except Exception as e:
            return False, f"Error loading file: {str(e)}"

    def get_curve_names(self):
        """
        Returns a list of available curve mnemonics.
        """
        if not self.las:
            return []
        return [curve.mnemonic for curve in self.las.curves]

    def get_log_data(self):
        """
        Returns the log data as a Pandas DataFrame.
        Handles null values by converting them to NaN.
        """
        if not self.las:
            return pd.DataFrame()

        df = self.las.df()
        # Ensure depth is a column if it's the index (common in lasio)
        if df.index.name == "DEPTH":
            df.reset_index(inplace=True)

        return df

    def get_well_info(self):
        """
        Returns a dictionary containing well header information.
        """
        if not self.las:
            return {}

        info = {}
        # Attempt to extract common header fields
        for item in self.las.well:
            info[item.mnemonic] = item.value

        return info

    @staticmethod
    def get_las_files(directory):
        """
        Returns a list of .LAS files in the specified directory.
        """
        if not os.path.exists(directory):
            return []
        return [f for f in os.listdir(directory) if f.upper().endswith(".LAS")]
