# coding: utf-8

"""命令行火车票查看器

Usage:
    tickets [-gdtkz] <from> <to> <date>

Options:
    -h,--help   显示帮助菜单
    -g          高铁
    -d          动车
    -t          特快
    -k          快速
    -z          直达

Example:
    tickets 北京 上海 2016-10-10
    tickets -dg 成都 南京 2016-10-10
"""
from docopt import docopt

from stations import stations
from prettytable import PrettyTable
import requests

from colorama import init, Fore

init()

class TrainsCollection:

    header = '车次 车站 时间 历时 一等 二等 软卧 硬卧 硬座 无座'.split()

    def __init__(self, available_trains, options):
        """查询到的火车班次集合

        :param available_trains: 一个列表, 包含可获得的火车班次, 每个
                                 火车班次是一个字典
        :param options: 查询的选项, 如高铁, 动车, etc...
        """
        self.available_trains = available_trains
        self.options = options

    def _get_duration(self, raw_train):
        duration = raw_train.get('duration').replace(':', '小时') + '分'
        if duration.startswith('00'):
            return duration[4:]
        if duration.startswith('0'):
            return duration[1:]
        return duration
        
    @property
    def trains(self):
        for raw_train in self.available_trains:
            train_no = raw_train['train_code']
            initial = train_no[0].lower()
            if not self.options or initial in self.options:
                train = [
                    train_no,        
                    '\n'.join([Fore.GREEN + raw_train['from_station'] + Fore.RESET,
                              Fore.RED + raw_train['to_station'] + Fore.RESET]),
                    '\n'.join([Fore.GREEN + raw_train['start_time'] + Fore.RESET,
                               Fore.RED + raw_train['end_time'] + Fore.RESET]),
                    self._get_duration(raw_train),
                    raw_train['first_seat'],
                    raw_train['second_seat'],
                    raw_train['rw'],
                    raw_train['yw'],
                    raw_train['yz'],
                    raw_train['wz'],
                ]
                yield train

    def pretty_print(self):
        pt = PrettyTable()
        pt._set_field_names(self.header)
        for train in self.trains:
            pt.add_row(train)
        print(pt)

def cli():
    """command-line interface"""
    headers = {'Accept': '*/*',
               'Accept-Encoding':'gzip, deflate, br',
               'Accept-Language':'zh-CN,zh;q=0.9',
               'Connection':'Keep-Alive',
               'Host':'kyfw.12306.cn',
               'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
			   'Referer':'https://kyfw.12306.cn/otn/leftTicket/init'
			   }   
    arguments = docopt(__doc__)
    from_station = stations.get(arguments['<from>'])
    to_station = stations.get(arguments['<to>'])
    date = arguments['<date>']
    dateArr = date.split('-')
	#当月份或日期为个位数时需要在前面补0，否则会出错
    if len(dateArr[1]) == 1:
        date = '%s-%d%s-%s' %(dateArr[0],0,dateArr[1],dateArr[2])
    if len(dateArr[2]) == 1:
        date = '%s-%s-%d%s' %(dateArr[0],dateArr[1],0,dateArr[2])	
    # 获取参数
    options = ''.join([
        key for key, value in arguments.items() if value is True
    ])
    # 构建URL
    url = 'https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date={}&leftTicketDTO.from_station={}&leftTicketDTO.to_station={}&purpose_codes=ADULT'.format(
        date, from_station, to_station
    )
	# 添加verify=False参数不验证证书
    r = requests.get(url, headers=headers)
    try:
        data = r.json()['data']
    except BaseException:
        print(Fore.RED + '发生错误' + Fore.RESET)
        exit(1)
    result = data['result']
    available_trains = []
    for res in result:
        # 分割数据
        r_list = res.split("|")
        # 过滤数据
        r_dict = {
            'train_code': r_list[3],
            'train_no': r_list[2],
            'start_time': r_list[8],
            'end_time': r_list[9],
            'duration': r_list[10],
            'from_station': data['map'].get(r_list[6]),
            'to_station': data['map'].get(r_list[7]),
            'date': r_list[13],
            'business_seat': r_list[-5],
            'first_seat': r_list[-6],
            'second_seat': r_list[-7],
            'gjrw': r_list[-8],
            'rw': r_list[-9],
            'dw': r_list[-10],
            'yw': r_list[-11],
            'rz': r_list[-12],
            'yz': r_list[-13],
            'wz': r_list[-14],
            'qt': r_list[-15],
            'remark': r_list[1],
            'seat_type': r_list[-2],
            "from_station_no": r_list[16],
            "destinction_no": r_list[17],
        }
        # 数据重整 如过对应数据为"",因为显示出来得为"--",所以在这把字典所有的""="--"
        for key in r_dict:
            if r_dict[key] == "":
                r_dict[key] = '--'
        available_trains.append(r_dict)
    TrainsCollection(available_trains, options).pretty_print()
    
if __name__ == '__main__':
    cli()