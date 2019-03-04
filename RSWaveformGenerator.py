import numpy as np
import datetime

class RSWaveformGenerator():
    """
    Generates .wv files from I/Q for the AFQ 100B I/Q modulation generator
    
    RSWaveformGenerator(instrument)
        Initialises waveform generator read to upload to qcodes instrument
        If instrument is not provided, can generate and save .wv files
            but not upload to instrument
        
    self.generate_wave(I_data,Q_data,clock,markers)
        Generates waveform (R&S .wv format) from input data
        I_data must be vector of values in range (-1,1)
        Q_data must be vector of values in range (-1,1)
        clock is AWG sample rate, from 1kHz to 300MHz, or 600MHz
        markers is dict with entries 'marker1','marker2','marker3','marker4'
            Not all entries required, can omit uncessary marker lists
            Marker lists take form position/value [[0,0],[10,1],[50,0]]
            Example:
                markers = {}
                markers['marker1'] = [[0,0],[10,1],[50,0]]
                markers['marker2'] = [[0,1],[50,0]]
                markers['marker3'] = [[0,0]]
            Marker voltages reset to 0 immediately after all marker waveforms (not IQ waveform) end
    self.upload_wave()
        Uploads waveform from memory self.waveform to instrument and autoplays
        Change self.instrument_directory and self.instrument_filename to change upload location
    self.save_wave_file(local_filename)
        Saves self.waveform as .wv file to local_filename
    self.read_wave_file(local_filename)
        Reads contents of .wv file local_filename to self.waveform
    self.upload_wave_file(local_filename)
        Reads contents of .wv file local_filename to self.waveform
        then uploads to instrument and autoplays
    """
    def __init__(self,instrument=None):
        self.instrument = instrument
        
        self.instrument_directory = 'D:\\TEMP\\'
        self.instrument_filename = 'temp.wv'
        self.instrument_filepath = 'D:\\TEMP\\temp.wv'
        
        self.comment = ''
        self.copyright = ''
        self.normalise = False
        self.checks = False
        
        self.waveform = None
        self.max_samples = 100e6 #512e6 #Device memory 512MSa but generating long waveform is too memory intensive
        
    def generate_wave(self,I_data,Q_data,clock,markers=None): 
        # Sanity checks
        self.waveform = None
        I_data_len = len(I_data)
        Q_data_len = len(Q_data)
        if I_data_len > self.max_samples:
            raise ValueError('Number of samples {} exceeds max_samples {}'.format(I_data_len,self.max_samples))
        if I_data_len != Q_data_len:
            raise ValueError('I_data and Q_data are not same length ({},{})'.format(I_data_len,Q_data_len))
        
        I_data = np.array(I_data,dtype=np.single)
        Q_data = np.array(Q_data,dtype=np.single)
        
        # Format I,Q vectors into IQIQIQ...
        IQ_data_len = 2*I_data_len
        IQ_data = np.empty(IQ_data_len,dtype=np.single)
        IQ_data[0::2] = I_data
        IQ_data[1::2] = Q_data

        
        # If scaling is desired, normalise to peak vector length of 1.0
        if self.normalise:
            print('Normalising!')
            max_IQ_data = np.max(np.abs( I_data + 1j*Q_data ))
            IQ_data = IQ_data / max_IQ_data
            peak = 1.0
            max_IQ_data = 1.0
            rms = np.sqrt(np.mean(np.square(IQ_data[0::2])+np.square(IQ_data[1::2]))) / max_IQ_data
            crf = 20*np.log10(peak/rms) # Crest factor
        else:
            # If not scaling, ought to check for clipping (outside +/-1)
            # But this is really memory intensive for large sample lengths
            # Particularly the third one
            # So I made these optional
            if self.checks:
                if np.max(I_data) > 1.0 or np.min(I_data) < -1.0:
                    raise ValueError('I_data must be in range -1 to +1 if auto scaling is disabled.')
                if np.max(Q_data) > 1.0 or np.min(Q_data) < -1.0:
                    raise ValueError('Q_data must be in range -1 to +1 if auto scaling is disabled.')
                if np.max(np.abs( I_data + 1j*Q_data )) > 1.0:
                    raise ValueError('I/Q vector length must be <1 if auto scaling is disabled.')
            peak = 1.0
            rms = 1.0
            crf = 0.0
        
        # Convert IQ_data to int16
        # Range is 16 bits for analogue outputs
        # +1.0 ---> +32767
        #  0.0 --->      0
        # -1.0 ---> -32767
        IQ_data = np.floor(IQ_data*32767+0.5).astype(np.int16)
        
        
        # Generate wv file header and encode to binary
        header_tag_str = '{TYPE: SMU-WV, 0}'
        comment_str = ('' if self.comment == '' else '{{COMMENT: {}}}'.format(self.comment))
        copyright_str = ('' if self.copyright == '' else '{{COPYRIGHT: {}}}'.format(self.copyright))
        origin_info_str = '{ORIGIN INFO: Python}' # This field is ignored by the instrument
        level_offs_str = '{{LEVEL OFFS: {}, {}}}'.format(20*np.log10(1.0/rms),20*np.log10(1.0/peak))
        date_str = '{{DATE: {};{}}}'.format(datetime.datetime.now().isoformat()[0:10],datetime.datetime.now().isoformat()[11:19])
        clock_str = '{{CLOCK: {}}}'.format(clock)
        samples_str = '{{SAMPLES: {}}}'.format(I_data_len)
        
        waveform_header = '{}{}{}{}{}{}{}{}'.format(header_tag_str,comment_str,copyright_str,origin_info_str,level_offs_str,date_str,clock_str,samples_str).encode('ascii')

        
        # Generate markers
        waveform_markers = ''
        if markers:
            if type(markers) != dict:
                raise ValueError("Markers must be dict. Allowed entries are 'marker1','marker2','marker3','marker4'")
            waveform_markers += '{{CONTROL LENGTH: {}}}'.format(IQ_data_len)
            if 'marker1' in markers:
                waveform_markers += '{{MARKER LIST 1: {}}}'.format(self._generate_marker_string(markers['marker1']))
            if 'marker2' in markers:
                waveform_markers += '{{MARKER LIST 2: {}}}'.format(self._generate_marker_string(markers['marker2']))
            if 'marker3' in markers:
                waveform_markers += '{{MARKER LIST 3: {}}}'.format(self._generate_marker_string(markers['marker3']))
            if 'marker4' in markers:
                waveform_markers += '{{MARKER LIST 4: {}}}'.format(self._generate_marker_string(markers['marker4']))
        waveform_markers = waveform_markers.encode('ascii')
        
        
        # Convert IQ_data to bitstring with length header
        wv_file_IQ_data_bitstring = '{{WAVEFORM-{}: #'.format(2*IQ_data_len + 1).encode('ascii') + IQ_data.tostring() + '}'.encode('ascii')
        
        # Construct wv binary file in memory
        self.waveform = waveform_header + waveform_markers + wv_file_IQ_data_bitstring
        
        print('Waveform generated: {} samples, {} bytes'.format(I_data_len,len(self.waveform)))
        #return self.wv_file_bitstring
    
    def upload_wave(self):
        if not self.waveform:
            raise ValueError('Waveform not generated. Please run generate_wave() or read_wave_file()')
        if not self.instrument:
            raise ValueError('Instrument not provided. Please call RSWaveformGenerator(instrument)')
        
        self.instrument_filepath = self.instrument_directory + self.instrument_filename
        
        # Calculate binary data block prefix
        # Takes form of '#213'
        # First number is how many digits subsequent number has
        # Second number is number of subsequent bytes
        num_bytes = len(self.waveform)
        num_digits_bytes = len(str(num_bytes))
        binary_prefix = '\',#{}{}'.format(num_digits_bytes,num_bytes)
        
        print('Uploading {} bytes...'.format(num_bytes),end = '')
        
        #SCPI_command = ':SOUR:WAV:DATA \'' + self.instrument_filepath + binary_prefix
        SCPI_command = 'MMEM:DATA \'' + self.instrument_filepath + binary_prefix
        self.instrument.visa_handle.write_raw(SCPI_command.encode('ascii')+self.waveform)
        self.instrument.wvfile(self.instrument_filepath)
        
        print('\rUploaded {} bytes to {}'.format(num_bytes,self.instrument_filepath))
        
    def save_wave_file(self,local_filename):
        if not self.waveform:
            raise ValueError('Waveform not generated. Please run generate_wave() or read_wave_file()')
        with open(local_filename, mode='wb') as wv:
            wv.write(self.waveform)
    
    def read_wave_file(self,local_filename):
        with open(local_filename, mode='rb') as wv:
            self.waveform = wv.read()
        
    def upload_wave_file(self,local_filename):
        self.read_wave_file(local_filename)
        self.upload_wave()
        
    def _generate_marker_string(self,marker_array):
        if np.shape(marker_array)[1] != 2:
            raise ValueError('Marker array must be in format [[0,0],[20,1],[50,0]], even if one entry')
        
        marker_string = ''
        for point in marker_array:
            marker_string += '{}:{};'.format(point[0],point[1])
        return marker_string.rstrip(';')