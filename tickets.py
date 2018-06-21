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

import gevent
from urllib.parse import urlencode
import json


init()

class TrainsCollection:

    header = '车次 车站 时间 历时 商务座 一等 二等 高级软卧 软卧 动卧 硬卧 软座 硬座 无座'.split()

    def __init__(self, available_trains, date, options):
        """查询到的火车班次集合

        :param available_trains: 一个列表, 包含可获得的火车班次, 每个
                                 火车班次是一个字典
        :param options: 查询的选项, 如高铁, 动车, etc...
        """
        self.available_trains = available_trains
        self.options = options
        self.date = date
        

    def _get_duration(self, raw_train):
        duration = raw_train.get('duration').replace(':', '小时') + '分'
        if duration.startswith('00'):
            return duration[4:]
        if duration.startswith('0'):
            return duration[1:]
        return duration
        
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
                    '\n'.join([raw_train['business_seat'],raw_train['business_price']]),                    
                    '\n'.join([raw_train['first_seat'],raw_train['first_seat_price']] ),
                    '\n'.join([raw_train['second_seat'],raw_train['second_seat_price']]),
                    '\n'.join([raw_train['gjrw'],raw_train['gjrw_seat_price']]),                    
                    '\n'.join([raw_train['rw'],raw_train['rw_seat_price']]),
                    '\n'.join([raw_train['dw'],raw_train['dw_seat_price']]),                   
                    '\n'.join([raw_train['yw'],raw_train['yw_seat_price']]),
                    '\n'.join([raw_train['rz'],raw_train['rz_seat_price']]),
                    '\n'.join([raw_train['yz'],raw_train['yz_seat_price']]),
                    '\n'.join([raw_train['wz'],raw_train['wz_seat_price']]),
                ]
                yield train
                
    def get_price(self, train_no, from_station_no, destinction_no, seat_types, date):
        base_url = "https://kyfw.12306.cn/otn/leftTicket/queryTicketPrice?"
        parmas = {
            "train_no": train_no,
            "from_station_no": from_station_no,
            "to_station_no": destinction_no,
            "seat_types": seat_types,
            "train_date": date
        }
        url = base_url + urlencode(parmas)
        try:
            data = requests.get(url).text
        except Exception as e:
            print("获取票价失败"+"|"+e+"|"+url) 
        data = json.loads(data)
        data_dic = data["data"]
        price_dic = {
            "business_price": "--",
            "first_seat_price": "--",
            "second_seat_price": "--",
            "gjrw_seat_price": "--",
            "rw_seat_price": "--",
            "dw_seat_price": "--",
            "yw_seat_price": "--",
            "rz_seat_price": "--",
            "yz_seat_price": "--",
            "wz_seat_price": "--"
        }
        # 商务座票价
        if("A9" in data_dic.keys()):
            price_dic["business_price"] = data_dic["A9"]
        elif("p" in data_dic.keys()):
            price_dic["business_price"] = data_dic["p"]
        # 一等座
        if("M" in data_dic.keys()):
            price_dic["first_seat_price"] = data_dic["M"]
        # 二等座
        if("O" in data_dic.keys()):
            price_dic["second_seat_price"] = data_dic["O"]
        # 高级软卧
        if("A6" in data_dic.keys()):
            price_dic["gjrw_seat_price"] = data_dic["A6"]
        # 软卧
        if("A4" in data_dic.keys()):
            price_dic["rw_seat_price"] = data_dic["A4"]
        # 动卧
        if("F" in data_dic.keys()):
            price_dic["dw_seat_price"] = data_dic["F"]
        # 硬卧
        if("A3" in data_dic.keys()):
            price_dic["yw_seat_price"] = data_dic["A3"]
        # 软座
        if("A2" in data_dic.keys()):
            price_dic["rz_seat_price"] = data_dic["A2"]
        # 硬座
        if("A1" in data_dic.keys()):
            price_dic["yz_seat_price"] = data_dic["A1"]
        # 无座
        if("WZ" in data_dic.keys()):
            price_dic["wz_seat_price"] = data_dic["WZ"]
        return price_dic
    
    def get_one_price(self, available_train):
        # 调用获取票价的函数
        price_dict = self.get_price(available_train['train_no'] , available_train["from_station_no"] ,
                               available_train["destinction_no"] , available_train["seat_type"] , self.date)
        
        available_train.update(price_dict)   # 更新price_info_dict
        
    def add_price(self):
        tasks = []
        for available_train in self.available_trains:
            # 遍历获取每个车次字典,布置为协程任务,把任务加入tasks列表
            tasks.append(gevent.spawn(self.get_one_price,available_train))
        # 等待所有任务全部完成,才进行下移步
        gevent.joinall(tasks)
    
    def pretty_print(self):
        pt = PrettyTable()
        pt._set_field_names(self.header)
        self.add_price()
        for train in self.trains():
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
    TrainsCollection(available_trains, date, options).pretty_print()
    

    
if __name__ == '__main__':
    cli()