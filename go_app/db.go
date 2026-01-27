package main

import (
	"context"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

var errNotFound = fmt.Errorf("not found")

func openDB(ctx context.Context) (*pgxpool.Pool, error) {
	return pgxpool.New(ctx, normalizeDatabaseURL(os.Getenv("DATABASE_URL")))
}

func normalizeDatabaseURL(url string) string {
	if url == "" {
		return "postgres://user:password@localhost:5435/perf_test"
	}
	if strings.HasPrefix(url, "postgresql+asyncpg://") {
		return "postgres://" + strings.TrimPrefix(url, "postgresql+asyncpg://")
	}
	if strings.HasPrefix(url, "postgresql+psycopg://") {
		return "postgres://" + strings.TrimPrefix(url, "postgresql+psycopg://")
	}
	return url
}

func fetchOrder(ctx context.Context, db *pgxpool.Pool, orderID int) (*OrderResponse, error) {
	rows, err := db.Query(ctx, `
		SELECT
			o.id,
			o.user_id,
			o.address_id,
			o.quantity,
			o.status,
			o.total::float8,
			o.created_at,
			u.id,
			u.email,
			u.full_name,
			u.created_at,
			a.id,
			a.user_id,
			a.line1,
			a.line2,
			a.city,
			a.state,
			a.postal_code,
			a.created_at,
			oi.id,
			oi.product_id,
			oi.quantity,
			oi.unit_price::float8,
			p.name,
			p.sku,
			p.price::float8
		FROM orders o
		JOIN users u ON o.user_id = u.id
		JOIN addresses a ON o.address_id = a.id
		JOIN order_items oi ON oi.order_id = o.id
		JOIN products p ON oi.product_id = p.id
		WHERE o.id = $1
	`, orderID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var resp *OrderResponse
	for rows.Next() {
		var (
			order Order
			user  User
			addr  Address
			item  OrderItem
		)
		var (
			orderCreated time.Time
			userCreated  time.Time
			addrCreated  time.Time
			line2        *string
		)
		if err := rows.Scan(
			&order.ID,
			&order.UserID,
			&order.AddressID,
			&order.Quantity,
			&order.Status,
			&order.Total,
			&orderCreated,
			&user.ID,
			&user.Email,
			&user.FullName,
			&userCreated,
			&addr.ID,
			&addr.UserID,
			&addr.Line1,
			&line2,
			&addr.City,
			&addr.State,
			&addr.PostalCode,
			&addrCreated,
			&item.OrderItemID,
			&item.ProductID,
			&item.Quantity,
			&item.UnitPrice,
			&item.Name,
			&item.SKU,
			&item.Price,
		); err != nil {
			return nil, err
		}
		order.CreatedAt = orderCreated.Format(time.RFC3339Nano)
		user.CreatedAt = userCreated.Format(time.RFC3339Nano)
		addr.CreatedAt = addrCreated.Format(time.RFC3339Nano)
		addr.Line2 = line2

		if resp == nil {
			resp = &OrderResponse{
				Order:    order,
				User:     user,
				Address:  addr,
				Products: []OrderItem{},
			}
		}
		resp.Products = append(resp.Products, item)
	}

	if resp == nil {
		return nil, errNotFound
	}
	return resp, rows.Err()
}

func fetchOrderLite(ctx context.Context, db *pgxpool.Pool, orderID int) (*Order, error) {
	var order Order
	var created time.Time
	row := db.QueryRow(ctx, `
		SELECT id, user_id, address_id, quantity, status, total::float8, created_at
		FROM orders
		WHERE id = $1
	`, orderID)
	if err := row.Scan(
		&order.ID,
		&order.UserID,
		&order.AddressID,
		&order.Quantity,
		&order.Status,
		&order.Total,
		&created,
	); err != nil {
		if err == pgx.ErrNoRows {
			return nil, errNotFound
		}
		return nil, err
	}
	order.CreatedAt = created.Format(time.RFC3339Nano)
	return &order, nil
}
