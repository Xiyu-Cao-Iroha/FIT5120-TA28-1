# CalmPath App 使用说明

CalmPath 是一款面向墨尔本 CBD 通勤者的**感官友好步行路线**App。它不是单纯帮你找"最快"的路,而是根据实时行人拥挤度数据,比较几条候选步行路线,告诉你哪条相对没那么拥挤,并解释为什么推荐这一条 —— 方便对人群、噪音等高刺激环境比较敏感的用户,能更从容地规划出行。走到目的地之前,还能顺路看看附近有没有可以喘口气的"安静地点"。

> 当前版本已经把 Figma 原型的完整流程做出来了,包括偏好设置和安静地点推荐。路线和地址搜索支持接入 Google Maps 变成真实数据(需要团队配置 API key),没配置时自动用演示数据兜底。仍未实现的部分(真实地图可视化、下一小时预测等)见文末说明。

---

## 一、偏好设置:你对人群拥挤有多敏感

打开 App 后的第一屏是 **"Setup 1 of 1"**,标题是 **"How sensitive are you to pedestrian crowds?"**(你对行人拥挤有多敏感?)。

三个选项:

- Low sensitivity(低敏感度)
- Moderate sensitivity(中等敏感度)
- High sensitivity(高敏感度)

选一个之后点击 **Continue**(继续)才能往下走。这个偏好会影响接下来路线对比时"多拥挤才算拥挤"的判断标准 —— 敏感度选得越高,系统就越容易把一条路线判定为 High sensory(也就是更"严格"地帮你避开人群);选低敏感度则相反,容忍度更高。这个偏好在当前使用过程中会一直保留,如果想改,回到这一屏重新选就行。

---

## 二、输入起点和终点

第二屏是 **"Where would you like to go?"**(你想去哪里?),左上角有 **"‹ Setup"** 可以返回上一步改偏好。

- **CURRENT LOCATION**(当前位置):输入你的出发地
- **DESTINATION**(目的地):输入你要去的地方

两个输入框现在都是**搜索框**:输入两三个字之后,下方会弹出候选地点列表,点一个就能选中(选中后输入框会自动填成完整地址)。

- 如果后端配置了 Google Maps API key,搜索的是真实地址,可以输入墨尔本 CBD 附近任意地点。
- 如果没配置,会退回一个内置的 5 个地名小列表(拼写需完全一致才能搜到):
  - Flinders Street Station(弗林德斯街火车站)
  - State Library Victoria(维多利亚州立图书馆)
  - Melbourne Central(墨尔本中央商场)
  - Federation Square(联邦广场)
  - Queen Victoria Market(维多利亚女王市场)

如果没在候选列表里选,也可以**直接输入经纬度**,格式为 `纬度, 经度`,例如 `-37.8183, 144.9671`。

填好之后点击 **"Find sensory-friendly routes"**(寻找感官友好路线)。

**懒得手动输入?** 点击下方的 **"Use demo route"**(使用演示路线)按钮,会自动帮你填好一组有完整演示数据的起终点(弗林德斯街站 → 州立图书馆),可以直接体验完整效果。

### 输入校验

- 起点和终点不能相同,也不能留空,否则会在对应输入框下面出现红字提示,已经输入的内容不会被清空。
- 终点必须在系统配置的墨尔本 CBD 范围内,超出范围会在下一步提交后收到"目的地超出服务范围"的提示。

---

## 三、路线对比页:选一条更平静的路

提交后进入 **"Choose a calmer route"**(选择更平静的路线)页面,系统会返回 1-2 条候选路线,每张卡片包含:

| 信息 | 说明 |
|---|---|
| 路线名称 + 预计时长 | 例如"Direct route via main corridor · 12.5 min" |
| 感官等级标签 | `Low sensory`(低感官刺激,浅绿色)/ `High sensory`(高感官刺激,浅粉色)/ `Sensory information unavailable`(数据不可用,浅蓝色)—— **文字始终显示,不依赖颜色本身传达信息** |
| 推荐说明 | 一句话解释这条路线为什么被(不)推荐。如果你在第一步设置了拥挤敏感度偏好,推荐路线会显示"Recommended for your high crowd sensitivity preference."(根据你的高敏感度偏好推荐)这样的文案;否则显示拥挤度对比说明,比如"Recommended for comparatively lower pedestrian congestion than the alternatives." |
| 数据新鲜度 | 比如"Data updated just now."(数据刚刚更新),提示你看到的是不是最新数据 |

被系统推荐的那条路线,卡片边框会加粗高亮成墨绿色。

点击任意一张卡片,可以进入该路线的地图详情页。

### 两种特殊情况

- **某条路线没有足够数据**:会显示"Sensory information unavailable",并说明"no sensory-based recommendation could be made"(不会给出基于感官数据的推荐)—— 系统不会在数据不足时瞎猜。
- **所有路线都拥挤**:页面顶部会出现一条黄色提示"All available routes currently contain some congestion."(当前所有路线都存在一定拥挤),并且在推荐路线下方会说明:即便是推荐的这条,也"不是完全没有拥挤"(not congestion-free),不会误导你以为它是完美选项。

想换起终点?页面左上角点 **"‹ Destination"** 可以返回上一步重新输入。

---

## 四、路线详情页:看拥挤路段在哪

点击某条路线卡片后,进入类似"路线名 · 时长"为标题的详情页,包含:

1. **示意地图**:用简化的线条图展示这条路线,深绿实线代表平静路段,**红色虚线代表拥挤路段**,起点/终点分别用实心圆点和空心圆点标出。
2. **WHY THIS ROUTE**(为什么是这条路线)卡片:一句话小标题 + 详细说明文字。
3. **拥挤路段列表**:用文字列出每一段的感官等级和拥挤分数,即使不看地图也能完整了解情况(地图从来不是获取这些信息的唯一渠道)。
4. **路线详情**:时长、距离、数据覆盖率(有多少比例的路段有传感器数据支持判断)。

页面底部有两个按钮:**"Show quiet places"**(查看附近安静地点,见下一节)和 **"Back to comparison"**(返回路线对比页)。左上角 **"‹ Routes"** 也能返回对比页。

---

## 五、安静地点:找个地方喘口气

在路线详情页点击 **"Show quiet places"**,进入 **"Choose a quiet place"**(选择一个安静地点)页面:

- 地图上会用 **"+"** 标记出这条路线附近经过验证/收录的安静地点候选(图书馆、庭院等)。
- 点一个 **"+"** 标记,它会变成 **✓**,下方出现"SELECTED"(已选择)信息框,显示这个地点的名字。
- 点击 **"View refuge information"**(查看庇护点信息),进入该地点的详情页。

详情页会显示:

- 分类标签(比如"LIBRARY · QUIET INDOOR SPACE"图书馆/安静室内空间)
- 地址
- 设施说明(比如有没有座位、无障碍设施)
- **数据来源说明**:有的地点标注"Location information from selected City of Melbourne public datasets."(来自 City of Melbourne 公开数据集,真实可信),有的标注"Prototype location information for demonstration."(仅用于演示的原型数据)—— 系统不会把没把握的信息说得跟确认过的一样。
- 点击 **"Walk to this refuge"**(前往这个庇护点),会显示一句确认文字,告诉你这个地点距离你路线大概多远。这一步是原型阶段的模拟确认,并不是真实的步行导航。

如果附近没有找到符合条件的安静地点,会显示 **"No quiet places nearby"**(附近没有安静地点),并提供 **"Return to route"**(返回路线)按钮,不会为了凑数编造一个不存在的地点。

页面左上角 **"‹ Route"** / **"‹ Quiet places"** 可以逐级返回。

---

## 常见错误提示对照表

| 提示 | 含义 | 该怎么做 |
|---|---|---|
| 输入框下方红字"Search for a CBD location and select it..." | 起点/终点没有从候选列表里选中,或者两者相同 | 重新搜索并点选候选项,或改用"纬度, 经度"格式 |
| "Destination is outside the service area" | 终点不在墨尔本 CBD 服务范围内 | 换一个 CBD 范围内的目的地 |
| "No walking route found" | 找不到步行路线 | 换一组起终点试试 |
| "Pedestrian data temporarily unavailable"(可重试) | 后端暂时没有有效的行人数据快照 | 点击"Retry"重试,或稍后再试 |
| "Too many requests"(可重试) | 短时间内请求太多,被限流了 | 等一会儿再点"Retry" |
| "No quiet places nearby" | 这条路线附近 500 米内没有收录的安静地点 | 点"Return to route"返回,或换一条路线试试 |

---

## 关于 Google Maps 接入

路线搜索和地址搜索背后接的是 Google Maps Platform(Directions API + Places API),但只在后端配置了 API key 的情况下才会生效;没配置 key 时,两者都会自动退回到内置的演示数据,不会报错、也不会中断使用体验。你看到的路线是"真实计算的"还是"演示用的固定路线",目前界面上不会特别标注区分,如果需要确认,可以问负责部署的同学后端有没有配置这个 key。

即使接了 Google Maps 的真实路线/地址数据,**地图可视化本身仍然是简化的示意图**(灰色网格 + 路线线条),不是真的地图瓦片/街景——这是团队确认过的范围,只换数据不换视觉呈现,保持跟 Figma 原型一致的简洁风格。

## 目前还不支持的功能

以下几项仍然不在本版本范围内:

- **未来一小时拥挤趋势预测**(US 2.2)—— 明确不做 ML/AI 预测,本轮范围外。
- **真实地图可视化** —— 见上一节,数据可以是真的,但呈现方式还是示意图。
- **真实步行导航** —— "Walk to this refuge"只是界面确认,不会给出真实的分步导航。
- **账号系统、离线地图、逐步 GPS 导航** —— 均不在 MVP 范围内。

详见 [`CalmPath_App_Development_Requirements.md`](CalmPath_App_Development_Requirements.md) 第4节的范围说明。
