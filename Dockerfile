# 从官方的 pgvector 镜像出发。0.8.6 是 pgvector 版本，pg17 是 PostgreSQL 版本。
# 固定版本号而不是用 latest —— 这样半年后重建也是同一个环境。
FROM pgvector/pgvector:0.8.6-pg17

# 在这个镜像上追加安装 PGroonga（日语全文检索）。
# 分成几步：装下载工具 -> 添加 Groonga 的软件源 -> 装 PGroonga 本体和 MeCab 分词器 -> 清理缓存
RUN apt-get update && apt-get install -y -V --no-install-recommends \
      ca-certificates lsb-release wget \
 && wget https://packages.groonga.org/debian/groonga-apt-source-latest-$(lsb_release --codename --short).deb \
 && apt-get install -y -V ./groonga-apt-source-latest-$(lsb_release --codename --short).deb \
 && apt-get update \
 && apt-get install -y -V postgresql-17-pgdg-pgroonga groonga-tokenizer-mecab \
 && rm -rf /var/lib/apt/lists/* groonga-apt-source-latest-*.deb