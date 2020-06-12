# var-io模块介绍
v0.2.4
var-io是希望在使用jupyter环境时更方便的查看并管理变量<p>
Manage your variable in jupyter
## 安装
```
pip install var-io
```
## 功能
1. 跟踪并查看变量
2. 保存或载入变量
3. 删除已有变量
4. 更多功能...
## 工作模式
filter:默认跟踪所有变量<p>
choose：默认不跟踪变量
## 参数解释
method:工作方式，filter或choose<p>
strict:是否跟踪模块或callable的变量<p>
exclude_unsupported：是否屏蔽不支持的变量类型

## 示例
### filter模式
``` python
from var_io import VarHome
vh = VarHome(method = 'filter')    #filter模式初始化

vh.vars()         #查看当前追踪的变量

a = {"a":3,'b':4}           #创建测试变量
b = np.random.randn(200,20)
c = pd.Series([1,2,3])

vh.vars()         #查看变量
```
|   | is_supported | type          | size      | memory usage |
| - | ------------ | ------------- | --------- | ------------ |
| a | TRUE         | dict          | 2         | 240          |
| b | TRUE         | numpy.ndarray | (200, 20) | 32112        |
| c | TRUE         | Series        | (3,)      | 128          |
|   |              |               |           |              |
### choose模式
```python
from var_io import VarHome
vh = VarHome(method = 'choose')    #filter模式初始化

vh.vars()         #查看当前追踪的变量

a = {"a":3,'b':4}           #创建测试变量
b = np.random.randn(200,20)
c = pd.Series([1,2,3])
vh.vars()     #当前没有跟踪的变量
```

### 其他
```python
vh.save_data('./test.ipynbdata')    #保存目前跟踪的变量
vh.load_data('./test.ipynbdata')    #将保存的变量加载到当前命名空间中
```
```python
vh.del_var('a')           #将变量a从当前命名空间中删除
vh.reset_all()                #重置
vh.clear_list()           #清空当前跟踪的变量列表，只跟踪之后定义的变量
```
```python
vh.choose_var('a')        #跟踪变量a
vh.exclude_var('a')       #屏蔽变量a
```