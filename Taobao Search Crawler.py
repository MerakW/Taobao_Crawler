# 导入所需模块
from time import sleep        # 用于控制等待时间

# 导入 DrissionPage 库的浏览器控制类
from DrissionPage import ChromiumPage, ChromiumOptions

# 导入 CSV 文件操作模块
import csv
import json

# ===============================================
# 浏览器配置与初始化
# ===============================================

# 创建 Chromium 浏览器配置对象
co = ChromiumOptions()
# 禁用无头模式，显示浏览器窗口以便调试
co.headless(False)
# 禁止加载图片，减少网络请求和提升速度
co.set_argument('--blink-settings=imagesEnabled=false')
# 禁用自动播放策略，只允许用户手势触发播放
co.set_argument('--autoplay-policy=user-gesture-required')
# 禁用媒体播放始终允许的功能
co.set_argument('--disable-features=MediaPlaybackAlwaysAllow')

# 创建浏览器实例（基于配置）
dp = ChromiumPage(co)

# ===============================================
# 翻页操作函数
# ===============================================

def scroll_to_bottom():
    """滚动到页面底部"""
    print("正在滚动到页面底部...")
    dp.scroll.to_bottom()
    sleep(2)  # 等待页面加载

def find_next_page_button():
    """查找下一页按钮"""
    try:
        # 使用 class 属性定位下一页按钮，next-next 类名是下一页按钮特有的
        btn = dp.ele('@class:next-next')
        print("找到下一页按钮")
        return btn
    except Exception as e:
        print(f"未找到下一页按钮: {e}")
        return None

def click_next_page(btn):
    """点击下一页按钮"""
    try:
        btn.click()
        print("已点击下一页按钮")
        sleep(3)  # 等待页面加载
        return True
    except Exception as e:
        print(f"点击下一页按钮失败: {e}")
        return False

# ===============================================
# 数据采集与解析函数
# ===============================================

def collect_and_parse_data():
    """采集并解析页面数据"""
    print("收集接口响应数据包...")
    # 收集所有接口响应的数据包
    package_list = []
    for i in range(5):
        try:
            # 等待接口响应，设置超时时间
            r = dp.listen.wait(timeout=8)
            package_list.append(r)
            print(f"已收集到 {len(package_list)} 个数据包")
        except:
            # 超时说明没有更多数据包
            print("超时，停止收集数据包")
            break
    
    if package_list:
        print(f"共收集到 {len(package_list)} 个数据包，开始筛选最大数据包...")
        
        # 计算每个数据包的大小
        package_sizes = []
        for package in package_list:
            # 尝试获取响应内容的大小
            try:
                if hasattr(package.response, 'body'):
                    size = len(str(package.response.body))
                    package_sizes.append((package, size))
            except:
                continue
        
        # 筛选出size最大的数据包
        if package_sizes:
            largest_package = max(package_sizes, key=lambda x: x[1])[0]
            print(f"筛选到最大数据包，大小: {max(package_sizes, key=lambda x: x[1])[1]} 字节")
            
            # 保存原始数据包到本地文件以便分析
            try:
                with open('raw_response.txt', 'w', encoding='utf-8') as f:
                    f.write(str(largest_package.response.body))
                print("数据包已保存到 raw_response.txt 文件")
            except Exception as e:
                print(f"保存数据包失败: {e}")
            
            # 解析数据包
            try:
                # 检查响应类型
                print(f"响应类型: {type(largest_package.response.body)}")
                
                # 尝试解析 JSON 数据
                raw_content = ""
                if isinstance(largest_package.response.body, str):
                    raw_content = largest_package.response.body
                elif isinstance(largest_package.response.body, bytes):
                    raw_content = largest_package.response.body.decode('utf-8')
                else:
                    raw_content = str(largest_package.response.body)
                
                # 处理 JSONP 格式
                if raw_content.strip().startswith('mtopjsonp'):
                    print("检测到 JSONP 格式，正在处理...")
                    # 找到开始和结束的括号位置
                    start_index = raw_content.find('(')
                    end_index = raw_content.rfind(')')
                    if start_index != -1 and end_index != -1:
                        raw_content = raw_content[start_index+1:end_index]
                
                # 尝试解析 JSON 数据
                json_data = json.loads(raw_content)
                
                # 检查是否包含所需数据
                if 'data' in json_data and 'itemsArray' in json_data['data']:
                    items = json_data['data']['itemsArray']
                    print(f"解析到 {len(items)} 个商品")
                    
                    # 遍历商品列表
                    for item in items:
                        # 提取商品信息
                        item_id = item.get('item_id', '')
                        title = item.get('title', '').replace('<span class=H>', '').replace('</span>', '')
                        price = item.get('price', '')
                        realSales = item.get('realSales', '')
                        procity = item.get('procity', '')
                        nick = item.get('nick', '')
                        shopTitle = item.get('shopInfo', {}).get('title', '')
                        shopTag = item.get('shopTag', '')
                        isP4p = item.get('isP4p', '')
                        pic_path = item.get('pic_path', '')
                        auctionURL = item.get('auctionURL', '')
                        
                        # 构造商品字典
                        item_dict = {
                            'item_id': item_id,
                            'title': title,
                            'price': price,
                            'realSales': realSales,
                            'procity': procity,
                            'nick': nick,
                            'shopTitle': shopTitle,
                            'shopTag': shopTag,
                            'isP4p': isP4p,
                            'pic_path': pic_path,
                            'auctionURL': auctionURL
                        }
                        
                        # 打印商品信息（调试用）
                        print(item_dict)
                        
                        # 将商品数据写入 CSV 文件
                        with open(OUTPUT_CSV, 'a', newline='', encoding='utf-8-sig') as f:
                            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
                            writer.writerow(item_dict)
                else:
                    print("数据包格式不正确，未找到 itemsArray 字段")
            except Exception as e:
                print(f"解析数据包失败: {e}")
                import traceback
                print("错误详细信息:")
                print(traceback.format_exc())
        else:
            print("未获取到有效数据包")
    else:
        print("未监听到任何接口响应")

# ===============================================
# 数据存储配置
# ===============================================

# 定义输出文件名和 CSV 字段
OUTPUT_CSV = "taobao_search_results.csv"

# 定义 CSV 文件的字段列表（根据数据包结构选择有用字段）
CSV_FIELDS = [
    'item_id', 'title', 'price', 'realSales', 'procity', 'nick',
    'shopTitle', 'shopTag', 'isP4p', 'pic_path', 'auctionURL'
]

# 初始化 CSV 文件并写入表头
with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
    writer.writeheader()

# ===============================================
# 主程序
# ===============================================

def main():
    try:
        print("程序启动中...")
        
        # 启动 API 监听，指定要监听的接口
        print("启动 API 监听...")
        dp.listen.start('https://h5api.m.taobao.com/h5/mtop.relationrecommend.wirelessrecommend.recommend/2.0/')
        
        # 访问淘宝搜索页面（搜索关键词："修补鞋"）
        target_url = "https://s.taobao.com/search?boxFilterList=&clientPreloadId=preload_1773991989591&commend=all&ie=utf8&initiative_id=tbindexz_20170306&page=1&preLoadOrigin=https%3A%2F%2Fwww.taobao.com&q=%E4%BF%AE%E8%A1%A5%E9%9E%8B&search_type=item&sourceId=tb.index&spm=a21bo.jianhua%2Fa.search_hover.0&ssid=s5-e&tab=all"
        print(f"访问页面: {target_url}")
        dp.get(target_url)
        sleep(3)

        # 翻页循环
        page_count = 1
        while True:
            print(f"\n=== 正在处理第 {page_count} 页 ===")
            
            # 滚动到底部
            scroll_to_bottom()
            
            # 采集并解析页面数据
            collect_and_parse_data()
            
            # 查找下一页按钮
            next_btn = find_next_page_button()
            if next_btn:
                # 点击下一页
                if click_next_page(next_btn):
                    page_count += 1
                else:
                    print("点击下一页按钮失败，停止翻页")
                    break
            else:
                print("未找到下一页按钮，停止翻页")
                break
                
    except Exception as e:
        print(f"程序执行错误: {e}")
        import traceback
        print("错误详细信息:")
        print(traceback.format_exc())
    finally:
        # 关闭浏览器进程
        print("关闭浏览器...")
        dp.quit()
        print("\n浏览器已关闭")
        print("数据爬取完成，结果已保存到 taobao_search_results.csv 文件中。")

if __name__ == "__main__":
    main()