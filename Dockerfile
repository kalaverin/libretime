FROM php:7.4-fpm AS libretime-legacy

ENV LIBRETIME_CONFIG_FILEPATH=/etc/libretime/config.yml
ENV LIBRETIME_LOG_FILEPATH=php://stderr

ARG USER=libretime
ARG UID=1000
ARG GID=1000

RUN set -eux \
    && adduser --disabled-password --uid=$UID --gecos '' --no-create-home ${USER} \
    && install --directory --owner=${USER} /etc/libretime /srv/libretime

RUN set -eux \
    && DEBIAN_FRONTEND=noninteractive apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    gettext \
    libcurl4-openssl-dev \
    libfreetype6-dev \
    libjpeg62-turbo-dev \
    libonig-dev \
    libpng-dev \
    libpq-dev \
    libxml2-dev \
    libyaml-dev \
    libzip-dev \
    locales \
    unzip \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/* \
    && pecl install apcu yaml \
    && docker-php-ext-enable apcu yaml \
    && docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-install -j$(nproc) \
    bcmath \
    curl \
    exif \
    gd \
    gettext \
    mbstring \
    opcache \
    pdo_pgsql \
    pgsql \
    sockets \
    xml

COPY legacy/locale/locale.gen /etc/locale.gen
RUN locale-gen

RUN mv "$PHP_INI_DIR/php.ini-production" "$PHP_INI_DIR/php.ini"
COPY "legacy/install/php/libretime-legacy.ini" "$PHP_INI_DIR/conf.d/"

COPY --from=composer /usr/bin/composer /usr/local/bin/composer

WORKDIR /var/www/html

COPY legacy/composer.* ./
RUN composer --no-cache install --no-progress --no-interaction --no-dev --no-autoloader

COPY legacy .
RUN set -eux \
    && make locale-build \
    && composer --no-cache dump-autoload --no-interaction --no-dev

RUN mkdir -p /var/www/echo/retime/libretime && ln -sf /var/www/html \
    /var/www/echo/retime/libretime/legacy

USER ${UID}:${GID}

ARG LIBRETIME_VERSION
ENV LIBRETIME_VERSION=$LIBRETIME_VERSION
