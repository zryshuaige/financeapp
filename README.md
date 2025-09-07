<p>
<strong><h2>金融交易平台demo</h2></strong>
模拟交易平台的交易下单等功能，使用Django + Vue3
</p>

### 👀 Demo

- [Github链接](https://github.com/zryshuaige/financeapp/)

### 🎉 功能

- [√] 登录注册
- [√] 站点简介
- [√] Hitokoto 一言
- [√] AI嵌入问答
- [√] 模拟交易
- [√] 数据库修改

### ⚙️ 部署

- **安装** [node.js](https://nodejs.org/zh-cn/) **环境**

  > node > 16.16.0  
  > npm > 8.15.0

- 然后以 **管理员权限** 运行 `cmd` 终端，并 `cd` 到 项目根目录
- 在 `终端` 中输入：

```bash
# 安装 pnpm
npm install -g pnpm

# 安装依赖
pnpm install

# 运行
启动Django数据库
python manage.py runserver
启动前端预览
pnpm run dev

分别在http://localhost:5173/ 预览页面
和http://127.0.0.1:8000/admin/管理数据库


### 技术栈

- [Vue](https://cn.vuejs.org/)
- [Vite](https://vitejs.cn/vite3-cn/)
- [Django](https://www.djangoproject.com/)

### API
- [deepseek](https://platform.deepseek.com/usage)
- [Hitokoto 一言](https://hitokoto.cn/)

