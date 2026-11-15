/* ==========================================================
   Tribuna · Carrito de compras — interactividad
   ========================================================== */
(() => {
  // ---- Toast de notificación ----
  function showToast(msg, type = 'success') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = msg;
    toast.className = `toast toast--${type} toast--show`;
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => {
      toast.classList.remove('toast--show');
    }, 2800);
  }

  // ---- Actualizar badge del carrito ----
  function updateBadge(count) {
    const badge = document.getElementById('cart-badge');
    if (!badge) return;
    if (count > 0) {
      badge.textContent = count;
      badge.style.display = '';
      badge.classList.add('cart-badge--bounce');
      setTimeout(() => badge.classList.remove('cart-badge--bounce'), 300);
    } else {
      badge.style.display = 'none';
    }
  }

  // ---- Obtener CSRF token ----
  function getCSRF() {
    const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
  }

  // ---- Botón "Agregar al carrito" (página de detalle) ----
  document.querySelectorAll('.btn-agregar').forEach(btn => {
    btn.addEventListener('click', async () => {
      const productoId = btn.dataset.productoId;
      const url = btn.dataset.url;
      const talla = document.querySelector('input[name="talla"]:checked')?.value || 'M';

      btn.disabled = true;
      btn.textContent = 'Agregando…';

      try {
        const res = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRF(),
          },
          body: JSON.stringify({ producto_id: productoId, talla: talla }),
        });
        const data = await res.json();

        if (data.ok) {
          showToast(data.mensaje);
          updateBadge(data.badge);
          btn.textContent = '✓ Agregado';
          setTimeout(() => {
            btn.textContent = 'Agregar al carrito';
            btn.disabled = false;
          }, 1500);
        } else {
          showToast('Error al agregar al carrito', 'error');
          btn.textContent = 'Agregar al carrito';
          btn.disabled = false;
        }
      } catch {
        showToast('Error de conexión', 'error');
        btn.textContent = 'Agregar al carrito';
        btn.disabled = false;
      }
    });
  });

  // ---- Controles de cantidad en el carrito ----
  document.querySelectorAll('.qty-minus, .qty-plus').forEach(btn => {
    btn.addEventListener('click', async () => {
      const itemId = btn.dataset.itemId;
      const url = btn.dataset.url;
      const qtyEl = document.getElementById(`qty-${itemId}`);
      let qty = parseInt(qtyEl.textContent);

      qty = btn.classList.contains('qty-minus') ? qty - 1 : qty + 1;

      if (qty < 1) {
        // Eliminar el item
        const row = btn.closest('.cart-item');
        const removeUrl = row.querySelector('.cart-item__remove')?.dataset.url;
        if (removeUrl) {
          try {
            const res = await fetch(removeUrl, {
              method: 'POST',
              headers: { 'X-CSRFToken': getCSRF() },
            });
            const data = await res.json();
            row.classList.add('cart-item--removing');
            setTimeout(() => {
              row.remove();
              updateBadge(data.badge);
              updateSummary(data.total, data.cantidad_total);
              if (data.cantidad_total === 0) location.reload();
            }, 300);
          } catch { showToast('Error al eliminar', 'error'); }
        }
        return;
      }

      try {
        const res = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRF(),
          },
          body: JSON.stringify({ cantidad: qty }),
        });
        const data = await res.json();

        if (data.ok) {
          qtyEl.textContent = qty;
          const subtotalEl = document.getElementById(`subtotal-${itemId}`);
          if (subtotalEl) subtotalEl.textContent = `$${data.subtotal.toLocaleString('es-CO')}`;
          updateBadge(data.badge);
          updateSummary(data.total, data.cantidad_total);
        }
      } catch { showToast('Error al actualizar', 'error'); }
    });
  });

  // ---- Botón eliminar item ----
  document.querySelectorAll('.cart-item__remove').forEach(btn => {
    btn.addEventListener('click', async () => {
      const itemId = btn.dataset.itemId;
      const url = btn.dataset.url;
      const row = btn.closest('.cart-item');

      try {
        const res = await fetch(url, {
          method: 'POST',
          headers: { 'X-CSRFToken': getCSRF() },
        });
        const data = await res.json();

        row.classList.add('cart-item--removing');
        setTimeout(() => {
          row.remove();
          updateBadge(data.badge);
          updateSummary(data.total, data.cantidad_total);
          if (data.cantidad_total === 0) location.reload();
        }, 300);
      } catch { showToast('Error al eliminar', 'error'); }
    });
  });

  // ---- Actualizar resumen del carrito ----
  function updateSummary(total, count) {
    const countEl = document.getElementById('summary-count');
    const totalEl = document.getElementById('summary-total');
    const grandEl = document.getElementById('summary-grand-total');
    const formatted = `$${total.toLocaleString('es-CO')}`;
    if (countEl) countEl.textContent = count;
    if (totalEl) totalEl.textContent = formatted;
    if (grandEl) grandEl.textContent = formatted;
  }
})();
