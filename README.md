# RSWaveformGenerator
Generates Rohde &amp; Schwarz .wv waveform files using Python, and provides commands to upload to and control Rohde & Schwarz AFQ VNAs.

This is a [QCoDeS-based](https://github.com/QCoDeS/Qcodes) Python driver to generate I/Q waveforms with markers for Rohde & Schwarz AFQ100A and AFQ100B arbitrary waveform generators. It enables vectors of I/Q data to be converted R&S's ``.wv`` waveform format and uploaded to the device, along with the necessary commands for remote control of the device.

To communicate with the R&S AWG you need both ``.py`` files. A typical use-case example is provided in the IPython notebook [``AWGtest.ipynb``](AWGtest.ipynb).

If all you need it to generate R&S ``.wv`` waveform files locally using Python, you just need [``RSWaveformGenerator.py``](RSWaveformGenerator.py), and an example script is provided in [``WVtest.ipynb``](WVtest.ipynb).
