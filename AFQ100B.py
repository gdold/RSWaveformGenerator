from qcodes import VisaInstrument, validators as vals
from qcodes.utils.helpers import create_on_off_val_mapping       
from RSWaveformGenerator import RSWaveformGenerator

class RohdeSchwarz_AFQ100B(VisaInstrument):
    """
	Rohde & Schwarz AFQ 100B
    UWB signal and I/Q modulation generator
    
    Subclass RSWaveformGenerator
    """

    def __init__(self, name, address, **kwargs):
        super().__init__(name, address, terminator='\n', **kwargs)
        
        self.waveform = RSWaveformGenerator(self)
        
        self.add_parameter(name='clock',
                           label='Clock',
                           unit='Hz',
                           get_cmd=':SOUR:TSIG:CLOC?',
                           set_cmd=':SOUR:TSIG:CLOC {:.3f}',
                           get_parser=float,
                           vals=vals.Numbers(1e3, 600e6)) # Actually 1kHz-300MHz, or 600MHz.
        self.add_parameter(name='amplitude',
                           label='Amplitude',
                           unit='V',
                           get_cmd='SOUR:OUTP:ANAL:BAL:AMPL?',
                           set_cmd='SOUR:OUTP:ANAL:BAL:AMPL {:.3f}V',
                           get_parser=float,
                           vals=vals.Numbers(0, 0.7))
        
        
        self.add_parameter('output',
                           label='Output',
                           get_cmd=':OUTP:STAT?',
                           set_cmd=':OUTP:STAT {}',
                           val_mapping=create_on_off_val_mapping(on_val='1',
                                                                 off_val='0'))
        self.add_parameter('source',
                           label='Baseband source',
                           get_cmd=':SOUR:STAT?',
                           set_cmd=':SOUR:STAT {}',
                           val_mapping=create_on_off_val_mapping(on_val='1',
                                                                 off_val='0'))
        self.add_parameter('activeoutput',
                           label='Active output',
                           get_cmd=':OUTP:AOUT?',
                           set_cmd=':OUTP:AOUT {}',
                           vals=vals.Enum('BBO', 'DIG')) # Ours only supports BBO, I think
        
        
        self.add_parameter('wvfile',
                           label='Waveform file',
                           get_cmd=':SOUR:WAV:SEL?',
                           set_cmd=':SOUR:WAV:SEL \'{}\'')
        
        
        self.add_parameter('runmode',
                           label='Trigger run mode',
                           get_cmd=':SOUR:TRIG:MODE?',
                           set_cmd=':SOUR:TRIG:MODE {}',
                           vals=vals.Enum('CONT','SING','REPN')) # Continuous, Single, or Repeat N times
        self.add_parameter('repeatcount',
                           label='Repeat count',
                           get_cmd=':SOUR:TRIG:RCO?',
                           set_cmd=':SOUR:TRIG:RCO {}',
                           get_parser=int,
                           vals=vals.Ints(1,100)) # Up to 100 repetitions, only for REPN runmode
        self.add_parameter('triggersource',
                           label='Trigger source',
                           get_cmd=':SOUR:TRIG:SOUR?',
                           set_cmd=':SOUR:TRIG:SOUR {}',
                           vals=vals.Enum('MAN','EXT','BUS','AUTO'))


        self.add_function('reset', call_cmd='*RST')
        self.add_function('run_self_tests', call_cmd='*TST?')

        self.connect_message()

    def on(self):
        self.source('on')
        self.output('on')

    def off(self):
        self.source('off')
        self.output('off')
    
    def trigger(self):
        self.write(':SOUR:TRIG:EXEC')