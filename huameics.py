import cv2
import requests
import re
import os
from PIL import Image
from paddleocr import PaddleOCR

# 定义fofa链接
fofa_url = 'https://search.censys.io/search?resource=hosts&sort=RELEVANCE&per_page=25&virtual_hosts=EXCLUDE&q=%E5%8D%8E%E8%A7%86%E7%BE%8E%E8%BE%BE'

# 尝试从fofa链接提取IP地址和端口号，并去除重复项
def extract_unique_ip_ports(fofa_url):
    try:
        response = requests.get(fofa_url)
        html_content = response.text
        # 使用正则表达式匹配IP地址和端口号
        ips_ports = re.findall(r'(\\d+\\.\\d+\\.\\d+\\.\\d+:\\d+)', html_content)
        unique_ips_ports = list(set(ips_ports))  # 去除重复的IP地址和端口号
        return unique_ips_ports if unique_ips_ports else None
    except requests.RequestException as e:
        print(f"请求错误: {e}")
        return None

# 检查视频流的可达性
def check_video_stream_connectivity(ip_port, url):
    try:
        video_url = f"http://{ip_port}{url}"
        cap = cv2.VideoCapture(video_url)
        if not cap.isOpened():
            print(f"视频URL {video_url} 无效")
            return None
        else:
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"视频URL {video_url} 的分辨率为 {width}x{height}")
            if width > 0 and height > 0:
                return video_url  # 返回有效的视频URL
        cap.release()
    except Exception as e:
        print(f"访问 {ip_port} 失败: {e}")
    return None

# 从视频流中获取华美视达的logo并使用OCR识别
def get_logo(video_url):
    try:
        video_capture = cv2.VideoCapture(video_url)
        if not video_capture.isOpened():
            print(f"{video_url}无效")
            return None
        ret, frame = video_capture.read()
        if not ret:
            print("Error reading frame. Exiting.")
            return None
        temp_file = 'temp.png'
        cv2.imwrite(temp_file, frame)
        image = Image.open(temp_file)
        gray_image = image.convert('L')
        gray_image.save(temp_file)
        ocr = PaddleOCR(use_angle_cls=True, lang='ch')
        img_array = np.array(gray_image)
        result = ocr.ocr(img_array, cls=True)
        if result is None:
            print("OCR 识别不到文字。")
            return None
        else:
            for line in result:
                if line is None:
                    continue
                boxes = line[0]
                text = line[0][0][0]
                score = line[0][0][1]
                print(f"Text: {text}, Score: {score}, Boxes: {boxes}")
                if text:
                    return text
    finally:
        os.remove(temp_file)
        video_capture.release()

# 遍历IP地址和端口号，获取华美视达的播放列表
def generate_playlist(unique_ips_ports, url):
    playlist = []
    for ip_port in unique_ips_ports:
        video_url = check_video_stream_connectivity(ip_port, url)
        if video_url:
            logo = get_logo(video_url)
            if logo:
                playlist.append(f"{logo},{video_url}")
    return playlist

# 定义需要检查的视频流URL后缀
urls_udp = "/hls/1/index.m3u8"

# 提取唯一的IP地址和端口号
unique_ips_ports = extract_unique_ip_ports(fofa_url)

if unique_ips_ports:
    playlist = generate_playlist(unique_ips_ports, urls_udp)
    # 将播放列表写入文件
    with open('bofang.txt', 'w', encoding='utf-8') as file:
        for item in playlist:
            file.write(item + '\n')
    print("播放列表已生成并保存到bofang.txt")
else:
    print("没有提取到IP地址和端口号。")