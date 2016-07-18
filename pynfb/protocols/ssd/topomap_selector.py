from PyQt4 import QtGui
from pynfb.protocols.ssd.ssd import ssd_analysis
from pynfb.protocols.ssd.sliders import Sliders
from pynfb.protocols.ssd.topomap_canvas import TopographicMapCanvas
from pynfb.protocols.ssd.interactive_barplot import ClickableBarplot

from pynfb.widgets.parameter_slider import ParameterSlider
from numpy import arange, dot, array, eye
from numpy.linalg import pinv



class TopomapSelector(QtGui.QWidget):
    def __init__(self, data, pos, names=None, sampling_freq=500, **kwargs):
        super(TopomapSelector, self).__init__(**kwargs)

        # layouts
        layout = QtGui.QHBoxLayout()
        layout.setMargin(0)
        v_layout = QtGui.QVBoxLayout()
        v_layout.addLayout(layout)
        self.setLayout(v_layout)

        # Sliders
        self.sliders = Sliders()
        self.sliders.apply_button.clicked.connect(self.recompute_ssd)
        v_layout.addWidget(self.sliders)

        # ssd properetires
        self.x_left = 4
        self.x_right = 40
        self.x_delta = 1
        self.freqs = arange(self.x_left, self.x_right, self.x_delta)
        self.pos = pos
        self.names = names
        self.data = data
        self.sampling_freq = sampling_freq

        # topomap canvas init
        self.topomap = TopographicMapCanvas(width=5, height=4, dpi=100)
        layout.addWidget(self.topomap, 1)

        # selector barplot init
        self.selector = ClickableBarplot(self)
        layout.addWidget(self.selector, 2)
        self.selector.changed.connect(self.underline_central_band)

        # first ssd analysis
        self.recompute_ssd()

    def select_action(self):
        index = self.selector.current_index()
        self.topomap.update_figure(self.topographies[index], self.pos, names=self.names)

    def get_current_topo(self):
        return self.topographies[self.selector.current_index()]

    def get_current_filter(self, reject=False):
        filters = self.filters[self.selector.current_index()]
        filter = filters[:, 0]
        if reject:
            rejected_matrix = dot(filters, eye(filters.shape[0]) - dot(filter[:, None], filter[None, :]))
            inv = pinv(filters)
            return dot(rejected_matrix, inv)
        return filter

    def get_current_bandpass(self):
        x1 = self.selector.current_x()
        x2 = x1 + self.x_delta
        return x1 - self.flanker_margin - self.flanker_delta, x2 + self.flanker_margin + self.flanker_delta

    def recompute_ssd(self):
        current_x = self.selector.current_x()
        parameters = self.sliders.getValues()
        self.x_delta = parameters['bandwidth']
        self.freqs = arange(self.x_left, self.x_right, self.x_delta)
        self.flanker_delta = parameters['flanker_bandwidth']
        self.flanker_margin = parameters['flanker_margin']
        self.major_vals, self.topographies, self.filters = ssd_analysis(self.data,
                                                                        sampling_frequency=self.sampling_freq,
                                                                        freqs=self.freqs,
                                                                        regularization_coef=parameters['regularizator'],
                                                                        flanker_delta=self.flanker_delta,
                                                                        flanker_margin=self.flanker_margin)
        self.selector.plot(self.freqs, self.major_vals)
        self.selector.set_current_by_value(current_x)
        self.select_action()

    def underline_central_band(self):
        self.selector.clear_underlines_and_ticks()
        x1 = self.selector.current_x()
        x2 = x1 + self.x_delta
        self.selector.underline(x1 - self.flanker_margin - self.flanker_delta, x1 - self.flanker_margin, 'flanker')
        self.selector.underline(x2 + self.flanker_margin, x2 + self.flanker_margin + self.flanker_delta, 'flanker')
        self.selector.underline(x1, x2, 'central')
        self.selector.add_xtick(x1 - self.flanker_margin - self.flanker_delta)
        self.selector.add_xtick(x2 + self.flanker_margin + self.flanker_delta)


if __name__ == '__main__':
    app = QtGui.QApplication([])

    import numpy as np
    from pynfb.widgets.helpers import ch_names_to_2d_pos
    ch_names = ['Fc1', 'Fc3', 'Fc5', 'C1', 'C3', 'C5', 'Cp1', 'Cp3', 'Cp5', 'Cz', 'Pz',
                'Cp2', 'Cp4', 'Cp6', 'C2', 'C4', 'C6', 'Fc2', 'Fc4', 'Fc6']
    channels_names = np.array(ch_names)
    x = np.loadtxt('example_recordings.txt')[:, channels_names!='Cz']
    channels_names = list(channels_names[channels_names!='Cz'])
    # x = np.random.randn(10000, len(channels_names))

    print(x.shape, channels_names)
    pos = ch_names_to_2d_pos(channels_names)
    widget = TopomapSelector(x, pos, names=channels_names, sampling_freq=1000)
    widget.show()
    app.exec_()
