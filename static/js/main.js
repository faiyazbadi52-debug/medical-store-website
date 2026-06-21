document.addEventListener('DOMContentLoaded', () => {
    // --- Global Notifications / Toast Handler ---
    const toastContainer = document.getElementById('toast-container');
    
    function showToast(message, type = 'success') {
        if (!toastContainer) return;
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        let icon = '<i class="fa-solid fa-circle-check"></i>';
        if (type === 'error') {
            icon = '<i class="fa-solid fa-triangle-exclamation"></i>';
        } else if (type === 'info') {
            icon = '<i class="fa-solid fa-circle-info"></i>';
        }
        
        toast.innerHTML = `
            ${icon}
            <span>${message}</span>
        `;
        
        toastContainer.appendChild(toast);
        
        // Remove toast after 4 seconds
        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) reverse forwards';
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, 4000);
    }

    // Export showToast globally for inline templates
    window.showToast = showToast;

    // --- Mobile Burger Menu ---
    const burgerBtn = document.getElementById('burger-menu-btn');
    const navLinksMenu = document.getElementById('nav-links-menu');
    
    if (burgerBtn && navLinksMenu) {
        burgerBtn.addEventListener('click', () => {
            navLinksMenu.classList.toggle('active');
            burgerBtn.classList.toggle('active');
        });
    }

    // --- Dynamic Search & Filters (Catalog Page) ---
    const searchInput = document.getElementById('catalog-search-input');
    const categoryFilters = document.querySelectorAll('.category-filter');
    const priceSlider = document.getElementById('price-slider');
    const priceSliderValue = document.getElementById('price-slider-value');
    const clearFiltersBtn = document.getElementById('btn-clear-filters');
    const medCards = document.querySelectorAll('.med-card');
    const noResultsBanner = document.getElementById('no-results-banner');
    
    // Function to apply filters in real-time
    function applyFilters() {
        if (!medCards.length) return;
        
        const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
        const maxPrice = priceSlider ? parseFloat(priceSlider.value) : 100;
        
        // Gather selected categories
        const selectedCategories = [];
        categoryFilters.forEach(checkbox => {
            if (checkbox.checked) {
                selectedCategories.push(checkbox.value);
            }
        });
        
        let visibleCount = 0;
        
        medCards.forEach(card => {
            const nameAndGeneric = card.getAttribute('data-name').toLowerCase();
            const category = card.getAttribute('data-category');
            const price = parseFloat(card.getAttribute('data-price'));
            
            // Filter match criteria
            const matchesSearch = query === '' || nameAndGeneric.includes(query);
            const matchesPrice = price <= maxPrice;
            const matchesCategory = selectedCategories.length === 0 || selectedCategories.includes(category);
            
            if (matchesSearch && matchesPrice && matchesCategory) {
                card.style.display = 'flex';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });
        
        // Show/hide no results banner
        if (noResultsBanner) {
            noResultsBanner.style.display = visibleCount === 0 ? 'block' : 'none';
        }
    }
    
    // Wire up filter event listeners
    if (searchInput) {
        searchInput.addEventListener('input', applyFilters);
    }
    
    categoryFilters.forEach(checkbox => {
        checkbox.addEventListener('change', applyFilters);
    });
    
    if (priceSlider) {
        priceSlider.addEventListener('input', (e) => {
            if (priceSliderValue) {
                priceSliderValue.textContent = `Max: ₹${e.target.value}`;
            }
            applyFilters();
        });
    }
    
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', () => {
            if (searchInput) searchInput.value = '';
            categoryFilters.forEach(checkbox => checkbox.checked = false);
            if (priceSlider) {
                priceSlider.value = 100;
                if (priceSliderValue) priceSliderValue.textContent = 'Max: ₹100';
            }
            applyFilters();
            showToast('Filters cleared successfully', 'info');
        });
    }

    // --- Medicine Details Modal Popup ---
    const detailsModal = document.getElementById('medicine-details-modal');
    const closeDetailsBtn = document.getElementById('btn-close-details-modal');
    const modalBodyContent = document.getElementById('details-modal-body-content');
    
    function attachModalTriggers() {
        const viewButtons = document.querySelectorAll('.btn-view-med-details');
        viewButtons.forEach(btn => {
            btn.addEventListener('click', async () => {
                const medId = btn.getAttribute('data-med-id');
                if (!detailsModal || !modalBodyContent) return;
                
                detailsModal.classList.add('active');
                modalBodyContent.innerHTML = `
                    <div style="text-align: center; padding: 2rem;">
                        <i class="fa-solid fa-spinner fa-spin" style="font-size: 2rem; color: var(--primary-teal);"></i>
                        <p style="margin-top: 1rem;">Loading chemical formulation details...</p>
                    </div>
                `;
                
                try {
                    const response = await fetch(`/api/medicine/${medId}`);
                    if (!response.ok) throw new Error('Failed to load medicine details.');
                    
                    const data = await response.json();
                    
                    let dosageIcon = '<i class="fa-solid fa-capsules"></i>';
                    if (data.dosage_form.toLowerCase() === 'tablet') {
                        dosageIcon = '<i class="fa-solid fa-tablets"></i>';
                    } else if (data.dosage_form.toLowerCase() === 'syrup') {
                        dosageIcon = '<i class="fa-solid fa-prescription-bottle"></i>';
                    }
                    
                    let stockHTML = '';
                    if (data.stock > 20) {
                        stockHTML = `<span style="color: var(--accent-emerald); font-weight: 600;"><i class="fa-solid fa-circle-check"></i> In Stock (${data.stock})</span>`;
                    } else if (data.stock > 0) {
                        stockHTML = `<span style="color: hsl(35, 100%, 45%); font-weight: 600;"><i class="fa-solid fa-triangle-exclamation"></i> Low Stock (${data.stock})</span>`;
                    } else {
                        stockHTML = `<span style="color: hsl(350, 75%, 50%); font-weight: 600;"><i class="fa-solid fa-circle-xmark"></i> Out of Stock</span>`;
                    }
                    
                    modalBodyContent.innerHTML = `
                        <div class="modal-med-header">
                            <div class="modal-med-icon">
                                ${dosageIcon}
                            </div>
                            <div class="modal-med-title-info">
                                <h3>${data.name}</h3>
                                <p class="generic">${data.generic_name}</p>
                                <span class="category">${data.category}</span>
                            </div>
                        </div>
                        
                        <div class="modal-med-details">
                            <div class="detail-block">
                                <h4>Manufacturer</h4>
                                <p>${data.manufacturer}</p>
                            </div>
                            <div class="detail-block">
                                <h4>Dosage Formulation</h4>
                                <p>${data.dosage_form.charAt(0).toUpperCase() + data.dosage_form.slice(1)}</p>
                            </div>
                            <div class="detail-block">
                                <h4>Unit Price</h4>
                                <p style="font-size: 1.25rem; font-weight: 800; color: var(--primary-teal)">₹${data.price.toFixed(2)}</p>
                            </div>
                            <div class="detail-block">
                                <h4>Inventory Status</h4>
                                <p>${stockHTML}</p>
                            </div>
                        </div>
                        
                        <div class="detail-block" style="margin-bottom: 2rem;">
                            <h4>Chemical Description / Usage</h4>
                            <p style="font-weight: 400; color: var(--text-muted); font-size: 0.95rem;">${data.description}</p>
                        </div>
                        
                        <div style="display: flex; gap: 15px;">
                            <button class="btn-checkout btn-add-cart-modal" 
                                    data-med-id="${data.id}" 
                                    style="flex-grow: 1;"
                                    ${data.stock <= 0 ? 'disabled' : ''}>
                                <i class="fa-solid fa-cart-plus"></i> ${data.stock <= 0 ? 'Out of Stock' : 'Add to Shopping Cart'}
                            </button>
                        </div>
                    `;
                    
                    // Wire up modal "Add to Cart" button
                    const modalAddCartBtn = modalBodyContent.querySelector('.btn-add-cart-modal');
                    if (modalAddCartBtn) {
                        modalAddCartBtn.addEventListener('click', () => {
                            addToCart(data.id);
                            detailsModal.classList.remove('active');
                        });
                    }
                    
                } catch (err) {
                    modalBodyContent.innerHTML = `
                        <div style="text-align: center; padding: 2rem; color: hsl(350, 75%, 50%);">
                            <i class="fa-solid fa-triangle-exclamation" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                            <h3>Error Loading Details</h3>
                            <p>${err.message}</p>
                        </div>
                    `;
                }
            });
        });
    }
    
    if (closeDetailsBtn) {
        closeDetailsBtn.addEventListener('click', () => {
            detailsModal.classList.remove('active');
        });
    }
    
    // Close modal on background click
    if (detailsModal) {
        detailsModal.addEventListener('click', (e) => {
            if (e.target === detailsModal) {
                detailsModal.classList.remove('active');
            }
        });
    }
    
    // Initialize Modal Triggers
    attachModalTriggers();

    // --- AJAX Cart Add Actions ---
    async function addToCart(medicineId, quantity = 1) {
        try {
            const response = await fetch('/api/cart/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ medicine_id: medicineId, quantity: quantity })
            });
            
            const data = await response.json();
            
            if (response.status === 401) {
                showToast('Please login to add items to your cart.', 'error');
                // Redirect to login page after brief pause
                setTimeout(() => {
                    window.location.href = '/login';
                }, 1500);
                return;
            }
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to add item to cart.');
            }
            
            // Update cart count badge
            const badge = document.getElementById('cart-badge-count');
            if (badge) {
                badge.textContent = data.cart_count;
            }
            
            showToast('Medicine added to cart successfully!', 'success');
            
        } catch (err) {
            showToast(err.message, 'error');
        }
    }
    
    // Wire up Catalog items Add-to-Cart
    const addToCartButtons = document.querySelectorAll('.btn-add-cart');
    addToCartButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation(); // Avoid triggering modal or card parent click
            const medId = btn.getAttribute('data-med-id');
            addToCart(medId);
        });
    });

    // --- AJAX Cart Quantity and Delete Updates (Cart Page) ---
    const quantityFields = document.querySelectorAll('.cart-qty-input-field');
    const decreaseQtyBtns = document.querySelectorAll('.btn-cart-qty-decrease');
    const increaseQtyBtns = document.querySelectorAll('.btn-cart-qty-increase');
    const removeCartItemBtns = document.querySelectorAll('.btn-cart-remove-item');
    
    // Function to calculate and update totals in DOM dynamically
    function recalculateCartUI(items) {
        let subtotal = 0;
        let savings = 0;
        
        items.forEach(item => {
            subtotal += item.price * item.quantity;
            // Savings is approximate difference between branded alternative and generic.
            // Branded alternative is estimated at 5x the cost of our generic.
            savings += (item.price * 4) * item.quantity; 
        });
        
        const tax = subtotal * 0.05;
        const total = subtotal + tax;
        
        // Update labels
        const subtotalEl = document.getElementById('summary-subtotal');
        const taxEl = document.getElementById('summary-tax');
        const totalEl = document.getElementById('summary-total');
        const savingsEl = document.getElementById('summary-savings');
        
        if (subtotalEl) subtotalEl.textContent = `₹${subtotal.toFixed(2)}`;
        if (taxEl) taxEl.textContent = `₹${tax.toFixed(2)}`;
        if (totalEl) totalEl.textContent = `₹${total.toFixed(2)}`;
        if (savingsEl) savingsEl.textContent = `₹${savings.toFixed(2)}`;
    }
    
    async function updateCartItemQuantity(itemId, newQty) {
        try {
            const response = await fetch('/api/cart/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ item_id: itemId, quantity: newQty })
            });
            
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Failed to update quantity.');
            
            // Update cart badge
            const badge = document.getElementById('cart-badge-count');
            if (badge) badge.textContent = data.cart_count;
            
            // Recalculate UI values
            recalculateCartUI(data.items);
            
        } catch (err) {
            showToast(err.message, 'error');
        }
    }
    
    // Hook quantity adjust buttons
    decreaseQtyBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const itemId = btn.getAttribute('data-item-id');
            const input = document.getElementById(`qty-input-${itemId}`);
            if (input) {
                let val = parseInt(input.value);
                if (val > 1) {
                    val--;
                    input.value = val;
                    updateCartItemQuantity(itemId, val);
                }
            }
        });
    });
    
    increaseQtyBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const itemId = btn.getAttribute('data-item-id');
            const input = document.getElementById(`qty-input-${itemId}`);
            if (input) {
                let val = parseInt(input.value);
                const max = parseInt(input.getAttribute('max'));
                if (val < max) {
                    val++;
                    input.value = val;
                    updateCartItemQuantity(itemId, val);
                } else {
                    showToast('Requested quantity exceeds available stock.', 'error');
                }
            }
        });
    });
    
    // Handlers for direct number input change
    quantityFields.forEach(input => {
        input.addEventListener('change', () => {
            const itemId = input.getAttribute('data-item-id');
            let val = parseInt(input.value);
            const min = parseInt(input.getAttribute('min')) || 1;
            const max = parseInt(input.getAttribute('max'));
            
            if (isNaN(val) || val < min) {
                val = min;
            } else if (val > max) {
                val = max;
                showToast('Quantity adjusted to maximum available stock.', 'info');
            }
            
            input.value = val;
            updateCartItemQuantity(itemId, val);
        });
    });
    
    // Remove cart item AJAX
    removeCartItemBtns.forEach(btn => {
        btn.addEventListener('click', async () => {
            const itemId = btn.getAttribute('data-item-id');
            const row = document.getElementById(`cart-item-row-${itemId}`);
            
            try {
                const response = await fetch('/api/cart/delete', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ item_id: itemId })
                });
                
                const data = await response.json();
                if (!response.ok) throw new Error(data.error || 'Failed to remove item.');
                
                // Animate removal
                if (row) {
                    row.style.opacity = '0';
                    row.style.transform = 'translateY(10px)';
                    row.style.transition = 'all 0.3s ease';
                    
                    setTimeout(() => {
                        row.remove();
                        // If no rows left, reload to show empty cart banner
                        if (data.items.length === 0) {
                            window.location.reload();
                        } else {
                            recalculateCartUI(data.items);
                        }
                    }, 300);
                }
                
                // Update badge
                const badge = document.getElementById('cart-badge-count');
                if (badge) badge.textContent = data.cart_count;
                
                showToast('Medicine removed from cart', 'info');
                
            } catch (err) {
                showToast(err.message, 'error');
            }
        });
    });
});
