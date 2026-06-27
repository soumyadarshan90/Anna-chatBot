import mysql.connector
import random

def get_connection():

    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="anna_eatery"
    )


def generate_order_id():

    return random.randint(1000, 9999)


def insert_order_item(food_item, quantity, order_id):

    try:

        conn = get_connection()

        cursor = conn.cursor()

        print(
            f"Inserting item={food_item}, qty={quantity}, order_id={order_id}"
        )

        cursor.callproc(
            'insert_order_item',
            (food_item, quantity, order_id)
        )

        conn.commit()

        cursor.close()
        conn.close()

        return 1

    except Exception as e:

        import traceback

        print("\nINSERT ORDER ITEM ERROR")
        print("ERROR:", e)

        traceback.print_exc()

        return -1


def insert_order_tracking(order_id, status):

    try:

        conn = get_connection()

        cursor = conn.cursor()

        query = """
        INSERT INTO order_tracking
        (order_id, status)
        VALUES (%s, %s)
        """

        cursor.execute(query, (order_id, status))

        conn.commit()

        cursor.close()
        conn.close()

        return 1

    except Exception as e:

        print("TRACKING ERROR:", e)

        return -1


def get_total_order_price(order_id):

    try:

        conn = get_connection()

        cursor = conn.cursor()

        query = """
        SELECT get_total_order_price(%s)
        """

        cursor.execute(query, (order_id,))

        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:

            return result[0]

        return 0

    except Exception as e:

        print("TOTAL PRICE ERROR:", e)

        return 0


def get_order_status(order_id):

    try:

        conn = get_connection()

        cursor = conn.cursor()

        query = """
        SELECT status
        FROM order_tracking
        WHERE order_id = %s
        """

        cursor.execute(query, (order_id,))

        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:

            return result[0]

        return None

    except Exception as e:

        print("STATUS ERROR:", e)

        return None