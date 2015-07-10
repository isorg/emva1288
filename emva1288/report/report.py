import jinja2
import os
import shutil
from collections import namedtuple
from tempfile import TemporaryDirectory

from .. results import Results1288
from .. plotting import Plotting1288, EVMA1288plots


def marketing(**kwargs):
    m = namedtuple('marketing',
                   'logo, vendor, model, '
                   'serial, sensor_type, sensor_name, '
                   'resolution_x, resolution_y, '
                   'sensor_diagonal, lens_mount, '
                   'shutter, overlap, readout_rate, '
                   'dark_current_compensation, interface, '
                   'watermark, qe_plot')

    # For these attributes default is False
    # for the rest is '-'
    kwargs.setdefault('logo', False)
    kwargs.setdefault('watermark', False)
    kwargs.setdefault('qe_plot', False)
    for field in m._fields:
        v = kwargs.pop(field, '-')
        setattr(m, field, v)
    return m


def op():
    o = namedtuple('op', 'bit_depth, gain,'
                   'offset, exposure_time, wavelength, '
                   'temperature, housing_temperature, '
                   'fpn_correction, results, plots, extra')

    o.bit_depth = '-'
    o.gain = '-'
    o.offset = '-'
    o.exposure_time = '-'
    o.wavelength = '-'
    o.temperature = 'room'
    o.housing_temperature = '-'
    o.fpn_correction = '-'
    o.extra = False
    o.results = None
    o.plots = None
    o.id = None
    return o

_CURRDIR = os.path.abspath(os.path.dirname(__file__))


class Report1288(object):
    def __init__(self, marketing):
        self._tmpdir = TemporaryDirectory()

        self.renderer = jinja2.Environment(
            block_start_string='%{',
            block_end_string='%}',
            variable_start_string='%{{',
            variable_end_string='%}}',
            comment_start_string='%{#',
            comment_end_string='%#}',
            loader=jinja2.FileSystemLoader(os.path.join(_CURRDIR, 'templates'))
        )
        self.ops = []
        self.marketing = marketing

    def _write_file(self, name, content):
        fname = os.path.join(self._tmpdir.name, name)
        with open(fname, 'w') as f:
            f.write(content)
        return fname

    def _stylesheet(self):
        stylesheet = self.renderer.get_template('emvadatasheet.sty')
        return stylesheet.render(marketing=self.marketing)

    def _report(self):
        report = self.renderer.get_template('report.tex')
        return report.render(marketing=self.marketing,
                             operation_points=self.ops)

    def latex(self, dir_):
        self._write_file('emvadatasheet.sty', self._stylesheet())
        self._write_file('report.tex', self._report())
        shutil.copytree(os.path.join(_CURRDIR, 'files'),
                        os.path.join(self._tmpdir.name, 'files'))
        outdir = os.path.abspath(dir_)
        os.makedirs(outdir)
        shutil.copytree(self._tmpdir.name, outdir)
        print('Report files found in:', outdir)
#         return os.path.relpath(dir_)

    def _results(self, data):
        return Results1288(data)

    def _plots(self, data, id_):
        res = self._results(data)
        plots = Plotting1288(res)
        savedir = os.path.join(self._tmpdir.name, id_)
        os.mkdir(savedir)
        plots.plot(savedir=savedir, show=False)
        names = {}
        for cls in EVMA1288plots:
            names[cls.__name__] = os.path.join(id_, cls.__name__ + '.pdf')
        return names

    def add(self, op, data=None):
        if not op.id:
            op.id = 'OP%d' % (len(self.ops) + 1)
        if not op.results and data:
            op.results = self._results(data).results
        if not op.plots and data:
            op.plots = self._plots(data, op.id)
        self.ops.append(op)

if __name__ == '__main__':
    r = Report1288(marketing)
#     print(r.report())

    import emva1288

    dir_ = '/home/work/1288/datasets/'
    fname = 'EMVA1288_ReferenceSet_003_Simulation_12Bit/EMVA1288_Data.txt'

    info = emva1288.ParseEmvaDescriptorFile(os.path.join(dir_, fname))
    imgs = emva1288.LoadImageData(info.info)
    dat = emva1288.Data1288(imgs.data)

    op1 = op()
    op1.gain = 333
    op1.offset = 444
    r.add(op1, dat)

#     op2 = op()
#     op2.gain = 111
#     op2.offset = 2222
# 
# 
#     r.add(op2)
    r.pdf()
#     print(r.report())