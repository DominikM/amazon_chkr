import json
from collections import deque
import argparse
import os
import readline
from pathlib import Path
import pickle

class SegmentTree:
    class Node:
        def __init__(self, parent, lowest, highest):
            self.lowest = lowest
            self.highest = highest
            self.left = None
            self.right = None
            self.parent = parent
            self.all_in = False

        def length(self):
            return self.highest - self.lowest

        def midpoint(self):
            return self.lowest + self.length() // 2

        def get_or_create_left(self):
            if self.left is None:
                self.left = self.__class__(self, self.lowest, self.midpoint())
                
            return self.left

        def get_or_create_right(self):
            if self.right is None:
                self.right = self.__class__(self, self.midpoint(), self.highest)

            return self.right

        def inside_range(self, low, high):
            if low <= self.lowest and high >= self.highest:
                return True

            return False

        def partially_overlaps_range(self, low, high):
            if low < self.lowest and  high > self.lowest:
                return True

            if low < self.highest and high > self.highest:
                return True

            return False

        def engulfs_range(self, low, high):
            if low >= self.lowest and high < self.highest:
                return True

            if low > self.lowest and high <= self.highest:
                return True

            return False

        def get_child(self, num):
            if num >= self.lowest and num < self.midpoint():
                return self.left

            elif num >= self.midpoint() and num < self.highest:
                return self.right

            else:
                return None

        def __str__(self):
            return f"Lowest: {self.lowest}; Highest: {self.highest}"
        

    def __init__(self, lowest, highest):
        self.top = self.Node(None, lowest, highest)
            
    def contains_num(self, num):
        node = self.top
        node_child = node.get_child(num)
        while node_child:
            node = node_child
            node_child = node_child.get_child(num)
            
        return node.all_in
        
                
    def insert_range(self, i_range):
        nodes_q = deque()
        nodes_q.append(self.top)

        while len(nodes_q) > 0:
            node = nodes_q.pop()

            if node.all_in:
                continue
            
            if node.inside_range(*i_range):
                node.all_in = True

            elif node.partially_overlaps_range(*i_range) or node.engulfs_range(*i_range):
                lnode = node.get_or_create_left()
                rnode = node.get_or_create_right()
                nodes_q.append(lnode)
                nodes_q.append(rnode)

        return self

    def insert_ranges(self, ranges):
        for i_range in ranges:
            self.insert_range(i_range)

        return self


def load_json(json_file_path):
    with open(json_file_path, 'r') as json_file:
        ip_file_str = json_file.read()
        ip_json = json.loads(ip_file_str)

    return ip_json

def read_json(ip_json):
    ranges = set()
    for ip_prefix_container in ip_json["prefixes"]:
        ip_prefix_str = ip_prefix_container["ip_prefix"]
        
        ip_combined = convert_ip_to_raw(ip_prefix_str.split("/")[0])
        mask = int(ip_prefix_str.split("/")[1])
        
        max_ip = 2 ** 32 - 1
        max_ip_with_mask = max_ip >> mask

        lowest_ip = ip_combined
        highest_ip = ip_combined | max_ip_with_mask

        ranges.add((lowest_ip, highest_ip+1))

    return ranges

def convert_ip_to_raw(ip):
    ips = list(map(lambda s: int(s), ip.split(".")))

    ip_combined = (ips[0] << 24) | (ips[1] << 16) | (ips[2] << 8) | ips[3]

    return ip_combined

def get_amazon_st(json_file_path):
    ip_json = load_json(json_file_path)
    ranges = read_json(ip_json)
    st = SegmentTree(0, 2**32)
    st.insert_ranges(ranges)
    return st

def contains_ip(st, ip):
    raw_ip = convert_ip_to_raw(ip)
    return st.contains_num(raw_ip)

def save_cache(st):
    home_dir = os.environ['HOME']
    cache_folder_path = os.path.join(home_dir, '.cache/amazon_chkr')
    Path(cache_folder_path).mkdir(parents=True, exist_ok=True)
    with open(os.path.join(cache_folder_path, 'data'), 'wb') as pickle_file:
        pickle.dump(st, pickle_file)

def get_cache():
    home_dir = os.environ['HOME']
    cache_path = os.path.join(home_dir, '.cache/amazon_chkr/data')

    if os.path.isfile(cache_path):
        with open(cache_path, 'rb') as cache_file:
            st = pickle.load(cache_file)

    else:
        print("No cache found.")
        json_file_path = input("Enter path for Amazon IPs JSON file: ")
        json_file = load_json(json_file_path)
        st = SegmentTree(0, 2**32).insert_ranges(read_json(json_file))
        save_cache(st)

    return st

st = get_amazon_st("/home/dominik/Downloads/ip-ranges.json")
def main():
    parser = argparse.ArgumentParser(description="Check if an IP address is Amazon owned")
    parser.add_argument('IP', type=str)
    args = parser.parse_args()

    st = get_cache()
    is_amazon = contains_ip(st, args.IP)

    if is_amazon:
        print("This is an Amazon IP.")
    else:
        print("This is not an Amazon IP.")
    

if __name__ == "__main__":
    main()



