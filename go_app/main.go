package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/redis/go-redis/v9"
)

type Order struct {
	ID        int     `json:"id"`
	UserID    int     `json:"user_id"`
	AddressID int     `json:"address_id"`
	Quantity  int     `json:"quantity"`
	Status    string  `json:"status"`
	Total     float64 `json:"total"`
	CreatedAt string  `json:"created_at"`
}

type User struct {
	ID        int    `json:"id"`
	Email     string `json:"email"`
	FullName  string `json:"full_name"`
	CreatedAt string `json:"created_at"`
}

type Address struct {
	ID         int     `json:"id"`
	UserID     int     `json:"user_id"`
	Line1      string  `json:"line1"`
	Line2      *string `json:"line2"`
	City       string  `json:"city"`
	State      string  `json:"state"`
	PostalCode string  `json:"postal_code"`
	CreatedAt  string  `json:"created_at"`
}

type OrderItem struct {
	OrderItemID int     `json:"order_item_id"`
	ProductID   int     `json:"product_id"`
	Name        string  `json:"name"`
	SKU         string  `json:"sku"`
	Price       float64 `json:"price"`
	Quantity    int     `json:"quantity"`
	UnitPrice   float64 `json:"unit_price"`
}

type OrderResponse struct {
	Order    Order       `json:"order"`
	User     User        `json:"user"`
	Address  Address     `json:"address"`
	Products []OrderItem `json:"products"`
}

func main() {
	ctx := context.Background()
	db, err := openDB(ctx)
	if err != nil {
		panic(err)
	}
	defer db.Close()

	rdb := redis.NewClient(&redis.Options{
		Addr: redisAddr(),
	})
	defer rdb.Close()

	appName := getenv("APP_NAME", "gin")
	cachePrefix := getenv("CACHE_PREFIX", fmt.Sprintf("orders:%s", appName))
	cacheTTL := getenvInt("ORDER_CACHE_TTL", 0)

	if err := clearCache(ctx, rdb, cachePrefix); err != nil {
		panic(err)
	}

	r := gin.Default()

	r.GET("/orders/:order_id", func(c *gin.Context) {
		orderID, err := strconv.Atoi(c.Param("order_id"))
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"detail": "Invalid order id"})
			return
		}

		cacheKey := fmt.Sprintf("%s:full:%d", cachePrefix, orderID)
		if payload, err := rdb.Get(ctx, cacheKey).Result(); err == nil {
			c.Data(http.StatusOK, "application/json", []byte(payload))
			return
		}

		resp, err := fetchOrder(ctx, db, orderID)
		if err == errNotFound {
			c.JSON(http.StatusNotFound, gin.H{"detail": "No orders found"})
			return
		}
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"detail": "DB error"})
			return
		}

		payload, _ := json.Marshal(resp)
		setCache(ctx, rdb, cacheKey, payload, cacheTTL)
		c.Data(http.StatusOK, "application/json", payload)
	})

	r.GET("/orders/:order_id/lite", func(c *gin.Context) {
		orderID, err := strconv.Atoi(c.Param("order_id"))
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"detail": "Invalid order id"})
			return
		}

		cacheKey := fmt.Sprintf("%s:lite:%d", cachePrefix, orderID)
		if payload, err := rdb.Get(ctx, cacheKey).Result(); err == nil {
			c.Data(http.StatusOK, "application/json", []byte(payload))
			return
		}

		order, err := fetchOrderLite(ctx, db, orderID)
		if err == errNotFound {
			c.JSON(http.StatusNotFound, gin.H{"detail": "No orders found"})
			return
		}
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"detail": "DB error"})
			return
		}

		payload, _ := json.Marshal(order)
		setCache(ctx, rdb, cacheKey, payload, cacheTTL)
		c.Data(http.StatusOK, "application/json", payload)
	})

	port := getenv("PORT", "8001")
	if err := r.Run("0.0.0.0:" + port); err != nil {
		panic(err)
	}
}

func redisAddr() string {
	url := os.Getenv("REDIS_URL")
	if url == "" {
		return "localhost:6379"
	}
	url = strings.TrimPrefix(url, "redis://")
	url = strings.TrimSuffix(url, "/0")
	return url
}

func getenv(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}

func getenvInt(key string, fallback int) int {
	if value := os.Getenv(key); value != "" {
		parsed, err := strconv.Atoi(value)
		if err == nil {
			return parsed
		}
	}
	return fallback
}

func setCache(ctx context.Context, rdb *redis.Client, key string, payload []byte, ttl int) {
	if ttl > 0 {
		_ = rdb.Set(ctx, key, payload, time.Duration(ttl)*time.Second).Err()
		return
	}
	_ = rdb.Set(ctx, key, payload, 0).Err()
}

func clearCache(ctx context.Context, rdb *redis.Client, prefix string) error {
	pattern := prefix + ":*"
	iter := rdb.Scan(ctx, 0, pattern, 1000).Iterator()
	var keys []string
	for iter.Next(ctx) {
		keys = append(keys, iter.Val())
		if len(keys) >= 1000 {
			if err := rdb.Del(ctx, keys...).Err(); err != nil {
				return err
			}
			keys = keys[:0]
		}
	}
	if err := iter.Err(); err != nil {
		return err
	}
	if len(keys) > 0 {
		if err := rdb.Del(ctx, keys...).Err(); err != nil {
			return err
		}
	}
	return nil
}
