#!/usr/bin/env python
# coding=utf-8


from vavava import scriptutils

class DLLiveConfig(scriptutils.BaseConfig):

    def get_ini_attrs(self):
        return {
            'default  |outpath  |s': None,
            'default  |channel  |s': None,
            'default  |liveurl  |s': None,
            'default  |addrfile |s': None,
            'default  |npf      |i': None,
            'default  |freq     |i': None,
            'network  |tmin     |i': None,
            'network  |tmax     |i': None,
            # 'proxy    |enable   |b': None,
            # 'proxy    |addr     |s': None,
            'favorites|         |s': lambda cfg: cfg.items('favorites'),
            '         |log      | ': scriptutils.get_log_from_config(),
            '         |proxyaddr| ': scriptutils.get_enabled_value_func('proxy', 'enable','addr'),
        }



    def get_args(self, argv):
        usage = """./dllive [-i|l][-c config][-o out_put_path][-f favorite][-d duration]"""
        import argparse
        parser=argparse.ArgumentParser(usage=usage, version='0.1')
        parser.add_argument('-c', '--config')
        parser.add_argument('-u', '--liveurl')
        parser.add_argument('-d', '--duration', type=float)
        parser.add_argument('-o', '--outpath',)
        parser.add_argument('-p', '--proxyaddr')
        parser.add_argument('-f', '--favorite')
        parser.add_argument('-i', '--interactive', action='store_true', default=False)
        parser.add_argument('-l', '--channellist', action='store_true', default=False)
        return parser.parse_args()


if __name__ == "__main__":
    import sys
    cfg = DLLiveConfig()
    cfg.read_cmdline_config('dllive.ini', argv=sys.argv)
    print cfg