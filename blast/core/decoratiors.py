import logging
import redis

r = redis.StrictRedis(host='localhost', port=6379, db=0)


def memoize_posts(key_pattern: str):
    def wrap(f):
        def wrapped_function(pk, start: int, end: int):
            key = key_pattern.format(pk)
            logging.info('Head up cache for {}'.format(key))

            if not r.exists(key):
                result = f(pk, start, end)

                if not result:
                    logging.info('Nothing to cache. Key is {}'.format(key))
                    return []

                if len(result) % 2:
                    logging.error('Invalid result size for {}. Size is {}'
                                  .format(key, len(result)))
                    return []

                r.zadd(key, *result)
            result = r.zrevrange(key, start, end)
            return [int(it) for it in result]
        return wrapped_function
    return wrap
